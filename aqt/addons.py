# Copyright: Ankitects Pty Ltd and contributors
# -*- coding: utf-8 -*-
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import io
import json
import re
import zipfile
import markdown
from send2trash import send2trash

from aqt.qt import *
from aqt.utils import showInfo, openFolder, isWin, openLink, \
    askUser, restoreGeom, saveGeom, showWarning, tooltip, getFile
from zipfile import ZipFile
import aqt.forms
import aqt
from aqt.downloader import download
from anki.lang import _
from anki.utils import intTime
from anki.sync import AnkiRequestsClient

class AddonManager:

    def __init__(self, mw):
        self.mw = mw
        self.dirty = False
        f = self.mw.form
        f.actionAdd_ons.triggered.connect(self.onAddonsDialog)
        sys.path.insert(0, self.addonsFolder())

    def allAddons(self):
        l = []
        for d in os.listdir(self.addonsFolder()):
            path = self.addonsFolder(d)
            if not os.path.exists(os.path.join(path, "__init__.py")):
                continue
            l.append(d)
        l.sort()
        if os.getenv("ANKIREVADDONS", ""):
            l = reversed(l)
        return l

    def managedAddons(self):
        return [d for d in self.allAddons()
                if re.match(r"^\d+$", d)]

    def addonsFolder(self, dir=None):
        root = self.mw.pm.addonFolder()
        if not dir:
            return root
        return os.path.join(root, dir)

    def loadAddons(self):
        for dir in self.allAddons():
            meta = self.addonMeta(dir)
            if meta.get("disabled"):
                continue
            self.dirty = True
            try:
                __import__(dir)
            except:
                showWarning(_("""\
An add-on you installed failed to load. If problems persist, please \
go to the Tools>Add-ons menu, and disable or delete the add-on.

When loading '%(name)s':
%(traceback)s
""") % dict(name=meta.get("name", dir), traceback=traceback.format_exc()))

    def onAddonsDialog(self):
        AddonsDialog(self)

    # Metadata
    ######################################################################

    def _addonMetaPath(self, dir):
        return os.path.join(self.addonsFolder(dir), "meta.json")

    def addonMeta(self, dir):
        path = self._addonMetaPath(dir)
        try:
            with open(path, encoding="utf8") as f:
                return json.load(f)
        except:
            return dict()

    def writeAddonMeta(self, dir, meta):
        path = self._addonMetaPath(dir)
        with open(path, "w", encoding="utf8") as f:
            json.dump(meta, f)

    def toggleEnabled(self, dir):
        meta = self.addonMeta(dir)
        meta['disabled'] = not meta.get("disabled")
        self.writeAddonMeta(dir, meta)

    def addonName(self, dir):
        return self.addonMeta(dir).get("name", dir)

    # Installing and deleting add-ons
    ######################################################################

    def installDownload(self, sid, data, name):
        try:
            zfile = ZipFile(io.BytesIO(data))
        except zipfile.BadZipfile:
            showWarning(_("The download was corrupt. Please try again."))
            return False
        
        mod = intTime()
        
        self.install(sid, zfile, name, mod)

    def installLocal(self, path):
        try:
            zfile = ZipFile(path)
        except zipfile.BadZipfile:
            return False, _("Corrupt add-on archive.")
        
        try:
            with zfile.open("manifest.json") as f:
                info = json.loads(f.read())
            package = info["package"]
            name = info["name"]
            mod = info.get("mod", None)
            assert isinstance(package, str) and isinstance(name, str)
            assert isinstance(mod, int) or mod is None
        except (KeyError, json.decoder.JSONDecodeError, AssertionError):
            # raised for missing manifest, invalid json, missing/invalid keys
            return False, _("Invalid add-on manifest.")
        
        self.install(package, zfile, name, mod)

        return name, None

    def install(self, dir, zfile, name, mod):
        # previously installed?
        meta = self.addonMeta(dir)
        base = self.addonsFolder(dir)
        if os.path.exists(base):
            self.backupUserFiles(dir)
            self.deleteAddon(dir)

        os.mkdir(base)
        self.restoreUserFiles(dir)

        # extract
        for n in zfile.namelist():
            if n.endswith("/"):
                # folder; ignore
                continue

            path = os.path.join(base, n)
            # skip existing user files
            if os.path.exists(path) and n.startswith("user_files/"):
                continue
            zfile.extract(n, base)

        # update metadata
        meta['name'] = name
        if mod is not None:  # allow packages to skip updating mod
            meta['mod'] = mod
        self.writeAddonMeta(dir, meta)

    def deleteAddon(self, dir):
        send2trash(self.addonsFolder(dir))

    # Processing local add-on files
    ######################################################################
    
    def processAPKX(self, paths):
        log = []
        errs = []
        self.mw.progress.start(immediate=True)
        for path in paths:
            base = os.path.basename(path)
            name, error = self.installLocal(path)
            if error:
                errs.append(_("Error installing <i>%(base)s</i>: %(error)s"
                              % dict(base=base, error=error)))
            else:
                log.append(_("Installed %(name)s" % dict(name=name)))
        self.mw.progress.finish()
        return log, errs

    # Downloading
    ######################################################################

    def downloadIds(self, ids):
        log = []
        errs = []
        self.mw.progress.start(immediate=True)
        for n in ids:
            ret = download(self.mw, n)
            if ret[0] == "error":
                errs.append(_("Error downloading %(id)s: %(error)s") % dict(id=n, error=ret[1]))
                continue
            data, fname = ret
            fname = fname.replace("_", " ")
            name = os.path.splitext(fname)[0]
            self.installDownload(str(n), data, name)
            log.append(_("Downloaded %(fname)s" % dict(fname=name)))
        self.mw.progress.finish()
        return log, errs

    # Updating
    ######################################################################

    def checkForUpdates(self):
        client = AnkiRequestsClient()

        # get mod times
        self.mw.progress.start(immediate=True)
        try:
            # ..of enabled items downloaded from ankiweb
            addons = []
            for dir in self.managedAddons():
                meta = self.addonMeta(dir)
                if not meta.get("disabled"):
                    addons.append(dir)

            mods = []
            while addons:
                chunk = addons[:25]
                del addons[:25]
                mods.extend(self._getModTimes(client, chunk))
            return self._updatedIds(mods)
        finally:
            self.mw.progress.finish()

    def _getModTimes(self, client, chunk):
        resp = client.get(
            aqt.appShared + "updates/" + ",".join(chunk))
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception("Unexpected response code from AnkiWeb: {}".format(resp.status_code))

    def _updatedIds(self, mods):
        updated = []
        for dir, ts in mods:
            sid = str(dir)
            if self.addonMeta(sid).get("mod",0) < ts:
                updated.append(sid)
        return updated

    # Add-on Config
    ######################################################################

    _configButtonActions = {}
    _configUpdatedActions = {}

    def addonConfigDefaults(self, dir):
        path = os.path.join(self.addonsFolder(dir), "config.json")
        try:
            with open(path, encoding="utf8") as f:
                return json.load(f)
        except:
            return None

    def addonConfigHelp(self, dir):
        path = os.path.join(self.addonsFolder(dir), "config.md")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return markdown.markdown(f.read())
        else:
            return ""

    def addonFromModule(self, module):
        return module.split(".")[0]

    def configAction(self, addon):
        return self._configButtonActions.get(addon)

    def configUpdatedAction(self, addon):
        return self._configUpdatedActions.get(addon)

    # Add-on Config API
    ######################################################################

    def getConfig(self, module):
        addon = self.addonFromModule(module)
        # get default config
        config = self.addonConfigDefaults(addon)
        if config is None:
            return None
        # merge in user's keys
        meta = self.addonMeta(addon)
        userConf = meta.get("config", {})
        config.update(userConf)
        return config

    def setConfigAction(self, module, fn):
        addon = self.addonFromModule(module)
        self._configButtonActions[addon] = fn

    def setConfigUpdatedAction(self, module, fn):
        addon = self.addonFromModule(module)
        self._configUpdatedActions[addon] = fn

    def writeConfig(self, module, conf):
        addon = self.addonFromModule(module)
        meta = self.addonMeta(addon)
        meta['config'] = conf
        self.writeAddonMeta(addon, meta)

    # user_files
    ######################################################################

    def _userFilesPath(self, sid):
        return os.path.join(self.addonsFolder(sid), "user_files")

    def _userFilesBackupPath(self):
        return os.path.join(self.addonsFolder(), "files_backup")

    def backupUserFiles(self, sid):
        p = self._userFilesPath(sid)
        if os.path.exists(p):
            os.rename(p, self._userFilesBackupPath())

    def restoreUserFiles(self, sid):
        p = self._userFilesPath(sid)
        bp = self._userFilesBackupPath()
        # did we back up userFiles?
        if not os.path.exists(bp):
            return
        os.rename(bp, p)

# Add-ons Dialog
######################################################################

class AddonsDialog(QDialog):

    def __init__(self, addonsManager):
        self.mgr = addonsManager
        self.mw = addonsManager.mw

        super().__init__(self.mw)

        f = self.form = aqt.forms.addons.Ui_Dialog()
        f.setupUi(self)
        f.getAddons.clicked.connect(self.onGetAddons)
        f.installFromFile.clicked.connect(self.onInstallFiles)
        f.checkForUpdates.clicked.connect(self.onCheckForUpdates)
        f.toggleEnabled.clicked.connect(self.onToggleEnabled)
        f.viewPage.clicked.connect(self.onViewPage)
        f.viewFiles.clicked.connect(self.onViewFiles)
        f.delete_2.clicked.connect(self.onDelete)
        f.config.clicked.connect(self.onConfig)
        self.form.addonList.currentRowChanged.connect(self._onAddonItemSelected)
        self.setAcceptDrops(True)
        self.redrawAddons()
        restoreGeom(self, "addons")
        self.show()

    def reject(self):
        saveGeom(self, "addons")
        return QDialog.reject(self)

    def redrawAddons(self):
        self.addons = [(self.annotatedName(d), d) for d in self.mgr.allAddons()]
        self.addons.sort()
        self.form.addonList.clear()
        self.form.addonList.addItems([r[0] for r in self.addons])
        if self.addons:
            self.form.addonList.setCurrentRow(0)

        self.form.addonList.repaint()

    def _onAddonItemSelected(self, row_int):
        try:
            addon = self.addons[row_int][1]
        except IndexError:
            addon = ''
        self.form.viewPage.setEnabled(bool (re.match(r"^\d+$", addon)))

    def annotatedName(self, dir):
        meta = self.mgr.addonMeta(dir)
        buf = self.mgr.addonName(dir)
        if meta.get('disabled'):
            buf += _(" (disabled)")
        return buf

    def selectedAddons(self):
        idxs = [x.row() for x in self.form.addonList.selectedIndexes()]
        return [self.addons[idx][1] for idx in idxs]

    def onlyOneSelected(self):
        dirs = self.selectedAddons()
        if len(dirs) != 1:
            showInfo(_("Please select a single add-on first."))
            return
        return dirs[0]

    def onToggleEnabled(self):
        for dir in self.selectedAddons():
            self.mgr.toggleEnabled(dir)
        self.redrawAddons()

    def onViewPage(self):
        addon = self.onlyOneSelected()
        if not addon:
            return
        if re.match(r"^\d+$", addon):
            openLink(aqt.appShared + "info/{}".format(addon))
        else:
            showWarning(_("Add-on was not downloaded from AnkiWeb."))

    def onViewFiles(self):
        # if nothing selected, open top level folder
        selected = self.selectedAddons()
        if not selected:
            openFolder(self.mgr.addonsFolder())
            return

        # otherwise require a single selection
        addon = self.onlyOneSelected()
        if not addon:
            return
        path = self.mgr.addonsFolder(addon)
        openFolder(path)

    def onDelete(self):
        selected = self.selectedAddons()
        if not selected:
            return
        if not askUser(ngettext("Delete the %(num)d selected add-on?",
                                "Delete the %(num)d selected add-ons?",
                                len(selected)) %
                               dict(num=len(selected))):
            return
        for dir in selected:
            self.mgr.deleteAddon(dir)
        self.redrawAddons()

    def onGetAddons(self):
        GetAddons(self)

    def onInstallFiles(self, paths=None):
        if not paths:
            key = (_("Packaged Anki Add-on") + " (*.apkx)")
            paths = getFile(self, _("Install Add-on(s)"), None, key,
                            key="addons", multi=True)
            if not paths:
                return False
        
        log, errs = self.mgr.processAPKX(paths)

        if log:
            tooltip("<br>".join(log), parent=self)
        if errs:
            msg = _("Please report this to the respective add-on author(s).")
            showWarning("<br><br>".join(errs + [msg]), parent=self)

        self.redrawAddons()

    def onCheckForUpdates(self):
        updated = self.mgr.checkForUpdates()
        if not updated:
            tooltip(_("No updates available."))
        else:
            names = [self.mgr.addonName(d) for d in updated]
            if askUser(_("Update the following add-ons?") +
                               "\n" + "\n".join(names)):
                log, errs = self.mgr.downloadIds(updated)
                if log:
                    tooltip("<br>".join(log), parent=self)
                if errs:
                    showWarning("<br><br>".join(errs), parent=self)

                self.redrawAddons()

    def onConfig(self):
        addon = self.onlyOneSelected()
        if not addon:
            return

        # does add-on manage its own config?
        act = self.mgr.configAction(addon)
        if act:
            act()
            return

        conf = self.mgr.getConfig(addon)
        if conf is None:
            showInfo(_("Add-on has no configuration."))
            return

        ConfigEditor(self, addon, conf)


# Fetching Add-ons
######################################################################

class GetAddons(QDialog):

    def __init__(self, dlg):
        QDialog.__init__(self, dlg)
        self.addonsDlg = dlg
        self.mgr = dlg.mgr
        self.mw = self.mgr.mw
        self.form = aqt.forms.getaddons.Ui_Dialog()
        self.form.setupUi(self)
        b = self.form.buttonBox.addButton(
            _("Browse Add-ons"), QDialogButtonBox.ActionRole)
        b.clicked.connect(self.onBrowse)
        restoreGeom(self, "getaddons", adjustSize=True)
        self.exec_()
        saveGeom(self, "getaddons")

    def onBrowse(self):
        openLink(aqt.appShared + "addons/2.1")

    def accept(self):
        # get codes
        try:
            ids = [int(n) for n in self.form.code.text().split()]
        except ValueError:
            showWarning(_("Invalid code."))
            return

        log, errs = self.mgr.downloadIds(ids)

        if log:
            tooltip("<br>".join(log), parent=self.addonsDlg)
        if errs:
            showWarning("<br><br>".join(errs))

        self.addonsDlg.redrawAddons()
        QDialog.accept(self)

# Editing config
######################################################################

class ConfigEditor(QDialog):

    def __init__(self, dlg, addon, conf):
        super().__init__(dlg)
        self.addon = addon
        self.conf = conf
        self.mgr = dlg.mgr
        self.form = aqt.forms.addonconf.Ui_Dialog()
        self.form.setupUi(self)
        restore = self.form.buttonBox.button(QDialogButtonBox.RestoreDefaults)
        restore.clicked.connect(self.onRestoreDefaults)
        self.setupFonts()
        self.updateHelp()
        self.updateText(self.conf)
        self.show()

    def onRestoreDefaults(self):
        default_conf = self.mgr.addonConfigDefaults(self.addon)
        self.updateText(default_conf)

    def setupFonts(self):
        font_mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.form.editor.setFont(font_mono)

    def updateHelp(self):
        txt = self.mgr.addonConfigHelp(self.addon)
        if txt:
            self.form.label.setText(txt)
        else:
            self.form.scrollArea.setVisible(False)

    def updateText(self, conf):
        self.form.editor.setPlainText(
            json.dumps(conf, ensure_ascii=False, sort_keys=True,
                       indent=4, separators=(',', ': ')))

    def accept(self):
        txt = self.form.editor.toPlainText()
        try:
            new_conf = json.loads(txt)
        except Exception as e:
            showInfo(_("Invalid configuration: ") + repr(e))
            return

        if not isinstance(new_conf, dict):
            showInfo(_("Invalid configuration: top level object must be a map"))
            return

        if new_conf != self.conf:
            self.mgr.writeConfig(self.addon, new_conf)
            # does the add-on define an action to be fired?
            act = self.mgr.configUpdatedAction(self.addon)
            if act:
                act(new_conf)

        super().accept()
