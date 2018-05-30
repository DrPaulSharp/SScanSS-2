import logging
import os
from enum import Enum, unique
from .model import MainWindowModel
from sscanss.ui.commands import ToggleRenderType


@unique
class MessageReplyType(Enum):
    Save = 1
    Discard = 2
    Cancel = 3


class MainWindowPresenter:
    def __init__(self, view):
        self.view = view
        self.model = MainWindowModel()

        self.recent_list_size = 10  # Maximum size of the recent project list

    def isProjectCreated(self):
        return True if self.model.project_data else False

    def createProject(self, name, instrument):
        """
        This function creates the stub data for the project

        :param name: The name of the project
        :type name: str
        :param instrument: The name of the instrument used for the project
        :type instrument: str
        """
        self.model.createProjectData(name, instrument)
        self.view.showProjectName(name)

    def saveProject(self, save_as=False):
        """
        This function saves a project to a file. A file dialog will be opened for the first save
        after which the function will save to the same location. if save_as id True a dialog is
        opened every time

        :param save_as: A flag denoting whether to use file dialog or not
        :type save_as: bool
        """
        if not self.isProjectCreated():
            return

        # Avoids saving when there are no changes
        if not self.model.unsaved and self.model.save_path and not save_as:
            return

        filename = self.model.save_path
        if save_as or not filename:
            filename = self.view.showSaveDialog('hdf5 File (*.h5)',
                                                current_dir=filename)
            if not filename:
                return

        try:
            self.model.saveProjectData(filename)
            self.updateRecentProjects(filename)
        except OSError:
            msg = 'A error occurred while attempting to save this project ({})'.format(filename)
            logging.error(msg)
            self.view.showErrorMessage(msg)

    def openProject(self, filename=''):
        """
        This function loads a project with the given filename. if filename is empty,
        a file dialog will be opened.

        :param filename: full path of file
        :type filename: str
        """
        if not self.confirmSave():
            return

        if not filename:
            filename = self.view.showOpenDialog('hdf5 File (*.h5)',
                                                current_dir=self.model.save_path)
            if not filename:
                return

        try:
            self.model.loadProjectData(filename)
            self.updateRecentProjects(filename)
            self.view.showProjectName(self.model.project_data['name'])
        except (KeyError, AttributeError):
            msg = '{} could not open because it has an incorrect format.'
            msg = msg.format(os.path.basename(filename))
            logging.error(msg)
            self.view.showErrorMessage(msg)
        except OSError:
            msg = 'An error occurred while opening this file.\nPlease check that ' \
                  'the file exist and also that this user has access privileges for this file.\n({})'

            msg = msg.format(filename)
            logging.error(msg)
            self.view.showErrorMessage(msg)

    def confirmSave(self):
        """
        Checks if the project is saved and asks the user to save if necessary

        :return: True if the project is saved or user chose to discard changes
        :rtype: bool
        """
        if not self.model.unsaved:
            return True

        reply = self.view.showSaveDiscardMessage(self.model.project_data['name'])

        if reply == MessageReplyType.Save:
            if self.model.save_path:
                self.saveProject()
                return True
            else:
                self.saveProject(save_as=True)
                return False if self.model.unsaved else True

        elif reply == MessageReplyType.Discard:
            return True

        else:
            return False

    def updateRecentProjects(self, new_entry):
        """
        This function adds a filename entry to the front of the recent projects list
        if it does not exist in the list. if the entry already exist, it is moved to the
        front but not duplicated.

        :param new_entry:
        :type new_entry: str]
        """
        projects = self.view.recent_projects
        projects.insert(0, new_entry)
        projects = list(dict.fromkeys(projects))
        if len(projects) <= self.recent_list_size:
            self.view.recent_projects = projects
        else:
            self.view.recent_projects = projects[:self.recent_list_size]

    def importSample(self, filename=''):
        if not filename:
            filename = self.view.showOpenDialog('STL File (*.stl)', current_dir=self.model.save_path)

            if not filename:
                return
        try:
            self.model.loadSample(filename)
            self.view.gl_widget.scene = self.model.sampleScene

        except:
            pass

    def toggleRenderType(self, render_type):
        toggle_command = ToggleRenderType(render_type, self.view.gl_widget,
                                          self.view.render_action_group)
        self.view.undo_stack.push(toggle_command)