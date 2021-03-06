# -*- coding: utf-8 -*-
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import datetime, time

from anki.schedulers import SCHEDULERS
from aqt.qt import *
import anki.lang
from aqt.utils import openFolder, openHelp, showInfo, askUser
import aqt
from anki.lang import _

class Preferences(QDialog):

    def __init__(self, mw):
        if not mw.col:
            showInfo(_("Please open a profile first."))
            return
        QDialog.__init__(self, mw, Qt.Window)
        self.mw = mw
        self.prof = self.mw.pm.profile
        self.form = aqt.forms.preferences.Ui_Preferences()
        self.form.setupUi(self)
        self.form.buttonBox.button(QDialogButtonBox.Help).setAutoDefault(False)
        self.form.buttonBox.button(QDialogButtonBox.Close).setAutoDefault(False)
        self.form.buttonBox.helpRequested.connect(lambda: openHelp("profileprefs"))
        self.silentlyClose = True
        self.setupLang()
        self.setupCollection()
        self.setupNetwork()
        self.setupBackup()
        self.setupOptions()
        self.show()

    def accept(self):
        # avoid exception if main window is already closed
        if not self.mw.col:
            return
        self.updateCollection()
        self.updateNetwork()
        self.updateBackup()
        self.updateOptions()
        self.mw.pm.save()
        self.mw.reset()
        self.done(0)
        aqt.dialogs.markClosed("Preferences")

    def reject(self):
        self.accept()

    # Language
    ######################################################################

    def setupLang(self):
        f = self.form
        f.lang.addItems([x[0] for x in anki.lang.langs])
        f.lang.setCurrentIndex(self.langIdx())
        f.lang.currentIndexChanged.connect(self.onLangIdxChanged)

    def langIdx(self):
        codes = [x[1] for x in anki.lang.langs]
        try:
            return codes.index(anki.lang.getLang())
        except:
            return codes.index("en")

    def onLangIdxChanged(self, idx):
        code = anki.lang.langs[idx][1]
        self.mw.pm.setLang(code)
        showInfo(_("Please restart Anki to complete language change."), parent=self)

    # Collection options
    ######################################################################

    def setupCollection(self):
        import anki.consts as c
        f = self.form
        qc = self.mw.col.conf
        self._setupDayCutoff()
        if isMac:
            f.hwAccel.setVisible(False)
        else:
            f.hwAccel.setChecked(self.mw.pm.glMode() != "software")
        f.lrnCutoff.setValue(qc['collapseTime']/60.0)
        f.timeLimit.setValue(qc['timeLim']/60.0)
        f.showEstimates.setChecked(qc['estTimes'])
        f.showProgress.setChecked(qc['dueCounts'])
        f.nightMode.setChecked(qc.get("nightMode", False))
        f.newSpread.addItems(list(c.newCardSchedulingLabels().values()))
        f.newSpread.setCurrentIndex(qc['newSpread'])
        f.useCurrent.setCurrentIndex(int(not qc.get("addToCur", True)))
        f.dayLearnFirst.setChecked(qc.get("dayLearnFirst", False))

        found_sched = False
        used_scheduler_name = str(qc.get('usedScheduler', 'anki.schedv2.Scheduler'))
        for scheduler_name, scheduler_data in SCHEDULERS.items():
            f.usedSched.insertItem(0, scheduler_data[0], (scheduler_name, scheduler_data[1]))
            if scheduler_name == used_scheduler_name:
                found_sched = True
                f.usedSched.setCurrentIndex(0)
        if not found_sched:
            f.usedSched.insertItem(0, used_scheduler_name, (used_scheduler_name, None))
            f.usedSched.setCurrentIndex(0)

    def updateCollection(self):
        f = self.form
        d = self.mw.col

        if not isMac:
            wasAccel = self.mw.pm.glMode() != "software"
            wantAccel = f.hwAccel.isChecked()
            if wasAccel != wantAccel:
                if wantAccel:
                    self.mw.pm.setGlMode("auto")
                else:
                    self.mw.pm.setGlMode("software")
                showInfo(_("Changes will take effect when you restart Anki."))

        qc = d.conf
        qc['dueCounts'] = f.showProgress.isChecked()
        qc['estTimes'] = f.showEstimates.isChecked()
        qc['newSpread'] = f.newSpread.currentIndex()
        qc['nightMode'] = f.nightMode.isChecked()
        qc['timeLim'] = f.timeLimit.value()*60
        qc['collapseTime'] = f.lrnCutoff.value()*60
        qc['addToCur'] = not f.useCurrent.currentIndex()
        qc['dayLearnFirst'] = f.dayLearnFirst.isChecked()
        qc['usedScheduler'] = f.usedSched.currentData()[0]
        self._updateDayCutoff()
        d.setMod()

    # Day cutoff
    ######################################################################

    def _setupDayCutoff(self):
        if self.mw.col.isFirstVersionSchedulerUsed():
            self._setupDayCutoffV1()
        else:
            self._setupDayCutoffV2()

    def _setupDayCutoffV1(self):
        self.startDate = datetime.datetime.fromtimestamp(self.mw.col.crt)
        self.form.dayOffset.setValue(self.startDate.hour)

    def _setupDayCutoffV2(self):
        self.form.dayOffset.setValue(self.mw.col.conf.get("rollover", 4))

    def _updateDayCutoff(self):
        if self.mw.col.isFirstVersionSchedulerUsed():
            self._updateDayCutoffV1()
        else:
            self._updateDayCutoffV2()

    def _updateDayCutoffV1(self):
        hrs = self.form.dayOffset.value()
        old = self.startDate
        date = datetime.datetime(
            old.year, old.month, old.day, hrs)
        self.mw.col.crt = int(time.mktime(date.timetuple()))

    def _updateDayCutoffV2(self):
        self.mw.col.conf['rollover'] = self.form.dayOffset.value()

    # Network
    ######################################################################

    def setupNetwork(self):
        self.form.syncOnProgramOpen.setChecked(
            self.prof['autoSync'])
        self.form.syncMedia.setChecked(
            self.prof['syncMedia'])
        if not self.prof['syncKey']:
            self._hideAuth()
        else:
            self.form.syncUser.setText(self.prof.get('syncUser', ""))
            self.form.syncDeauth.clicked.connect(self.onSyncDeauth)

    def _hideAuth(self):
        self.form.syncDeauth.setVisible(False)
        self.form.syncUser.setText("")
        self.form.syncLabel.setText(_("""\
<b>Synchronization</b><br>
Not currently enabled; click the sync button in the main window to enable."""))

    def onSyncDeauth(self):
        self.prof['syncKey'] = None
        self.mw.col.media.forceResync()
        self._hideAuth()

    def updateNetwork(self):
        self.prof['autoSync'] = self.form.syncOnProgramOpen.isChecked()
        self.prof['syncMedia'] = self.form.syncMedia.isChecked()
        if self.form.fullSync.isChecked():
            self.mw.col.modSchema(check=False)
            self.mw.col.setMod()

    # Backup
    ######################################################################

    def setupBackup(self):
        self.form.numBackups.setValue(self.prof['numBackups'])
        self.form.openBackupFolder.linkActivated.connect(self.onOpenBackup)

    def onOpenBackup(self):
        openFolder(self.mw.pm.backupFolder())

    def updateBackup(self):
        self.prof['numBackups'] = self.form.numBackups.value()

    # Basic & Advanced Options
    ######################################################################

    def setupOptions(self):
        self.form.pastePNG.setChecked(self.prof.get("pastePNG", False))

    def updateOptions(self):
        self.prof['pastePNG'] = self.form.pastePNG.isChecked()

