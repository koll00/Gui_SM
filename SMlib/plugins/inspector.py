# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see SMlib/__init__.py for details)

"""Object Inspector Plugin"""

from PyQt4.QtGui import (QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy,
                                QMenu, QToolButton, QGroupBox, QFontComboBox,
                                QActionGroup, QFontDialog, QWidget, QComboBox,
                                QLineEdit, QMessageBox)
from PyQt4.QtCore import SIGNAL, QUrl, QTimer, QThread

import re
import os.path as osp
import socket
import sys

# Local imports
from SMlib import dependencies
from SMlib.configs.baseconfig import get_conf_path, _
from SMlib.configs.ipythonconfig import IPYTHON_QT_MODULE, SUPPORTED_IPYTHON
from SMlib.config import CONF
from SMlib.configs.guiconfig import get_color_scheme, get_font, set_font
from SMlib.utils import programs
from SMlib.utils.qthelpers import (get_icon, create_toolbutton,
                                       add_actions, create_action)
from SMlib.widgets.comboboxes import EditableComboBox
from SMlib.widgets.sourcecode import codeeditor
from SMlib.widgets.findreplace import FindReplace
from SMlib.widgets.browser import WebView
from SMlib.widgets.externalshell.pythonshell import ExtPythonShellWidget
from SMlib.plugins import SMPluginWidget, PluginConfigPage

#XXX: Hardcoded dependency on optional IPython plugin component
#     that requires the hack to make this work without IPython
if programs.is_module_installed(IPYTHON_QT_MODULE, SUPPORTED_IPYTHON):
    from SMlib.widgets.ipython import IPythonControlWidget
else:
    IPythonControlWidget = None  # analysis:ignore

# Check for Sphinx presence to activate rich text mode
if programs.is_module_installed('sphinx', '>=0.6.6'):
    sphinx_version = programs.get_module_version('sphinx')
    from SMlib.utils.inspector.sphinxify import (CSS_PATH, sphinxify,
                                                     warning, generate_context)
else:
    sphinxify = sphinx_version = None  # analysis:ignore

# To add sphinx dependency to the Dependencies dialog
SPHINX_REQVER = '>=0.6.6'
dependencies.add("sphinx", _("Rich text help on the Object Inspector"),
                 required_version=SPHINX_REQVER)


class ObjectComboBox(EditableComboBox):
    """
    QComboBox handling object names
    """
    def __init__(self, parent):
        EditableComboBox.__init__(self, parent)
        self.object_inspector = parent
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.tips = {True: '', False: ''}
        
    def is_valid(self, qstr=None):
        """Return True if string is valid"""
        if qstr is None:
            qstr = self.currentText()
        if not re.search('^[a-zA-Z0-9_\.]*$', str(qstr), 0):
            return False
        objtxt = unicode(qstr)
        if self.object_inspector.get_option('automatic_import'):
            shell = self.object_inspector.internal_shell
            if shell is not None:
                return shell.is_defined(objtxt, force_import=True)
        shell = self.object_inspector.get_shell()
        if shell is not None:
            try:
                return shell.is_defined(objtxt)
            except socket.error:
                shell = self.object_inspector.get_shell()
                try:
                    return shell.is_defined(objtxt)
                except socket.error:
                    # Well... too bad!
                    pass
        
    def validate_current_text(self):
        self.validate(self.currentText())

class ObjectInspectorConfigPage(PluginConfigPage):
    def setup_page(self):
        sourcecode_group = QGroupBox(_("Source code"))
        wrap_mode_box = self.create_checkbox(_("Wrap lines"), 'wrap')
        names = CONF.get('color_schemes', 'names')
        choices = zip(names, names)
        cs_combo = self.create_combobox(_("Syntax color scheme: "),
                                        choices, 'color_scheme_name')

        sourcecode_layout = QVBoxLayout()
        sourcecode_layout.addWidget(wrap_mode_box)
        sourcecode_layout.addWidget(cs_combo)
        sourcecode_group.setLayout(sourcecode_layout)
        
        plain_text_font_group = self.create_fontgroup(option=None,
                                    text=_("Plain text font style"),
                                    fontfilters=QFontComboBox.MonospacedFonts)
        rich_text_font_group = self.create_fontgroup(option='rich_text',
                                text=_("Rich text font style"))
                                
        features_group = QGroupBox(_("Additional features"))
        math_box = self.create_checkbox(_("Render mathematical equations"),
                                        'math')
        req_sphinx = sphinx_version is not None and \
                     programs.is_module_installed('sphinx', '>=1.1')
        math_box.setEnabled(req_sphinx)
        if not req_sphinx:
            sphinx_tip = _("This feature requires Sphinx 1.1 or superior.")
            if sphinx_version is not None:
                sphinx_tip += "\n" + _("Sphinx %s is currently installed."
                                       ) % sphinx_version
            math_box.setToolTip(sphinx_tip)
        
        features_layout = QVBoxLayout()
        features_layout.addWidget(math_box)
        features_group.setLayout(features_layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(rich_text_font_group)
        vlayout.addWidget(plain_text_font_group)
        vlayout.addWidget(features_group)
        vlayout.addWidget(sourcecode_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)


class RichText(QWidget):
    """
    WebView widget with find dialog
    """
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        
        self.webview = WebView(self)
        self.find_widget = FindReplace(self)
        self.find_widget.set_editor(self.webview)
        self.find_widget.hide()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.webview)
        layout.addWidget(self.find_widget)
        self.setLayout(layout)
        
    def set_font(self, font, fixed_font=None):
        """Set font"""
        self.webview.set_font(font, fixed_font=fixed_font)
        
    def set_html(self, html_text, base_url):
        """Set html text"""
        self.webview.setHtml(html_text, base_url)
        
    def clear(self):
        self.set_html('', self.webview.url())
        
        
class PlainText(QWidget):
    """
    Read-only editor widget with find dialog
    """
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.editor = None

        # Read-only editor
        self.editor = codeeditor.CodeEditor(self)
        self.editor.setup_editor(linenumbers=False, language='py',
                                 scrollflagarea=False)
        self.connect(self.editor, SIGNAL("focus_changed()"),
                     lambda: self.emit(SIGNAL("focus_changed()")))
        self.editor.setReadOnly(True)
        
        # Find/replace widget
        self.find_widget = FindReplace(self)
        self.find_widget.set_editor(self.editor)
        self.find_widget.hide()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        layout.addWidget(self.find_widget)
        self.setLayout(layout)
        
    def set_font(self, font, color_scheme=None):
        """Set font"""
        self.editor.set_font(font, color_scheme=color_scheme)
        
    def set_color_scheme(self, color_scheme):
        """Set color scheme"""
        self.editor.set_color_scheme(color_scheme)
        
    def set_text(self, text, is_code):
        self.editor.set_highlight_current_line(is_code)
        self.editor.set_occurence_highlighting(is_code)
        if is_code:
            self.editor.set_language('py')
        else:
            self.editor.set_language(None)
        self.editor.set_text(text)
        self.editor.set_cursor_position('sof')
        
    def clear(self):
        self.editor.clear()


class SphinxThread(QThread):
    """
    A worker thread for handling rich text rendering.
    
    Parameters
    ----------
    text : dict
        A dict containing the doc string components to be rendered.
    html_text_no_doc : unicode
        Text to be rendered if doc string cannot be extracted.
    math_option : bool
        Use LaTeX math rendering.
        
    """
    def __init__(self, text={}, html_text_no_doc='', math_option=False):
        super(SphinxThread, self).__init__()
        self.text = text
        self.html_text_no_doc = html_text_no_doc
        self.math_option = math_option

    def run(self):
        html_text = self.html_text_no_doc
        text = self.text
        if text is not None and text['docstring'] != '':
            try:
                context = generate_context(name=text['name'],
                                           argspec=text['argspec'],
                                           note=text['note'],
                                           math=self.math_option)
                html_text = sphinxify(text['docstring'], context)
            except Exception, error:
                self.emit(SIGNAL('error_msg(QString)'), unicode(error))
                return
        self.emit(SIGNAL('html_ready(QString)'), html_text)


class ObjectInspector(SMPluginWidget):
    """
    Docstrings viewer widget
    """
    CONF_SECTION = 'inspector'
    CONFIGWIDGET_CLASS = ObjectInspectorConfigPage
    LOG_PATH = get_conf_path('.inspector')
    def __init__(self, parent):
        SMPluginWidget.__init__(self, parent)
        
        self.internal_shell = None

        # Initialize plugin
        self.initialize_plugin()

        self.no_doc_string = _("No documentation available")
        
        self._last_console_cb = None
        self._last_editor_cb = None

        self.set_default_color_scheme()

        self.plain_text = PlainText(self)
        self.rich_text = RichText(self)
        
        color_scheme = get_color_scheme(self.get_option('color_scheme_name'))
        self.set_plain_text_font(self.get_plugin_font(), color_scheme)
        self.plain_text.editor.toggle_wrap_mode(self.get_option('wrap'))
        
        # Add entries to read-only editor context-menu
        font_action = create_action(self, _("&Font..."), None,
                                    'font.png', _("Set font style"),
                                    triggered=self.change_font)
        self.wrap_action = create_action(self, _("Wrap lines"),
                                         toggled=self.toggle_wrap_mode)
        self.wrap_action.setChecked(self.get_option('wrap'))
        self.plain_text.editor.readonly_menu.addSeparator()
        add_actions(self.plain_text.editor.readonly_menu,
                    (font_action, self.wrap_action))

        self.set_rich_text_font(self.get_plugin_font('rich_text'))
        
        self.shell = None
        
        self.external_console = None
        
        # locked = disable link with Console
        self.locked = False
        self._last_texts = [None, None]
        self._last_rope_data = None
        
        # Object name
        layout_edit = QHBoxLayout()
        layout_edit.setContentsMargins(0, 0, 0, 0)
        txt = _("Source")
        if sys.platform == 'darwin':
            source_label = QLabel("  " + txt)
        else:
            source_label = QLabel(txt)
        layout_edit.addWidget(source_label)
        self.source_combo = QComboBox(self)
        self.source_combo.addItems([_("Console"), _("Editor")])
        self.connect(self.source_combo, SIGNAL('currentIndexChanged(int)'),
                     self.source_changed)
        if not programs.is_module_installed('rope'):
            self.source_combo.hide()
            source_label.hide()
        layout_edit.addWidget(self.source_combo)
        layout_edit.addSpacing(10)
        layout_edit.addWidget(QLabel(_("Object")))
        self.combo = ObjectComboBox(self)
        layout_edit.addWidget(self.combo)
        self.object_edit = QLineEdit(self)
        self.object_edit.setReadOnly(True)
        layout_edit.addWidget(self.object_edit)
        self.combo.setMaxCount(self.get_option('max_history_entries'))
        self.combo.addItems( self.load_history() )
        self.connect(self.combo, SIGNAL("valid(bool)"),
                     lambda valid: self.force_refresh())
        
        # Plain text docstring option
        self.docstring = True
        self.rich_help = sphinxify is not None \
                         and self.get_option('rich_mode', True)
        self.plain_text_action = create_action(self, _("Plain Text"),
                                               toggled=self.toggle_plain_text)
        
        # Source code option
        self.show_source_action = create_action(self, _("Show Source"),
                                                toggled=self.toggle_show_source)
        
        # Rich text option
        self.rich_text_action = create_action(self, _("Rich Text"),
                                         toggled=self.toggle_rich_text)
                        
        # Add the help actions to an exclusive QActionGroup
        help_actions = QActionGroup(self)
        help_actions.setExclusive(True)
        help_actions.addAction(self.plain_text_action)
        help_actions.addAction(self.rich_text_action)
        
        # Automatic import option
        self.auto_import_action = create_action(self, _("Automatic import"),
                                                toggled=self.toggle_auto_import)
        auto_import_state = self.get_option('automatic_import')
        self.auto_import_action.setChecked(auto_import_state)
        
        # Lock checkbox
        self.locked_button = create_toolbutton(self,
                                               triggered=self.toggle_locked)
        layout_edit.addWidget(self.locked_button)
        self._update_lock_icon()
        
        # Option menu
        options_button = create_toolbutton(self, text=_("Options"),
                                           icon=get_icon('tooloptions.png'))
        options_button.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(self)
        add_actions(menu, [self.rich_text_action, self.plain_text_action,
                           self.show_source_action, None,
                           self.auto_import_action])
        options_button.setMenu(menu)
        layout_edit.addWidget(options_button)

        if self.rich_help:
            self.switch_to_rich_text()
        else:
            self.switch_to_plain_text()
        self.plain_text_action.setChecked(not self.rich_help)
        self.rich_text_action.setChecked(self.rich_help)
        self.rich_text_action.setEnabled(sphinxify is not None)
        self.source_changed()

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(layout_edit)
        layout.addWidget(self.plain_text)
        layout.addWidget(self.rich_text)
        self.setLayout(layout)
        
        # Add worker thread for handling rich text rendering
        if sphinxify is None:
            self._sphinx_thread = None
        else:
            self._sphinx_thread = SphinxThread(text={},
                                  html_text_no_doc=warning(self.no_doc_string),
                                  math_option=self.get_option('math'))
            self.connect(self._sphinx_thread, SIGNAL('html_ready(QString)'), 
                         self._on_sphinx_thread_html_ready)
            self.connect(self._sphinx_thread, SIGNAL('error_msg(QString)'),
                         self._on_sphinx_thread_error_msg)

        self._starting_up = True
            
    #------ SMPluginWidget API ---------------------------------------------    
    def get_plugin_title(self):
        """Return widget title"""
        return _('Object inspector')
    
    def get_plugin_icon(self):
        """Return widget icon"""
        return get_icon('inspector.png')
    
    def get_focus_widget(self):
        """
        Return the widget to give focus to when
        this plugin's dockwidget is raised on top-level
        """
        self.combo.lineEdit().selectAll()
        return self.combo
    
    def get_plugin_actions(self):
        """Return a list of actions related to plugin"""
        return []
    
    def register_plugin(self):
        """Register plugin in Spyder's main window"""
        self.connect(self, SIGNAL('focus_changed()'),
                     self.main.plugin_focus_changed)
        self.main.add_dockwidget(self)
        self.main.console.set_inspector(self)
        self.internal_shell = self.main.console.shell
        
    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed"""
        return True
        
    def refresh_plugin(self):
        """Refresh widget"""
        if self._starting_up:
            self._starting_up = False
            QTimer.singleShot(5000, self.refresh_plugin)
        self.set_object_text(None, force_refresh=False)

    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings"""
        color_scheme_n = 'color_scheme_name'
        color_scheme_o = get_color_scheme(self.get_option(color_scheme_n))
        font_n = 'plugin_font'
        font_o = self.get_plugin_font()
        rich_font_n = 'rich_text'
        rich_font_o = self.get_plugin_font('rich_text')
        wrap_n = 'wrap'
        wrap_o = self.get_option(wrap_n)
        self.wrap_action.setChecked(wrap_o)
        math_n = 'math'
        math_o = self.get_option(math_n)
        if font_n in options:
            scs = color_scheme_o if color_scheme_n in options else None
            self.set_plain_text_font(font_o, color_scheme=scs)
        if rich_font_n in options:
            self.set_rich_text_font(rich_font_o)
        elif color_scheme_n in options:
            self.set_plain_text_color_scheme(color_scheme_o)
        if wrap_n in options:
            self.toggle_wrap_mode(wrap_o)
        if math_n in options:
            self.toggle_math_mode(math_o)
        
    #------ Public API (related to inspector's source) -------------------------
    def source_is_console(self):
        """Return True if source is Console"""
        return self.source_combo.currentIndex() == 0
    
    def switch_to_editor_source(self):
        self.source_combo.setCurrentIndex(1)
        
    def switch_to_console_source(self):
        self.source_combo.setCurrentIndex(0)
        
    def source_changed(self, index=None):
        if self.source_is_console():
            # Console
            self.combo.show()
            self.object_edit.hide()
            self.show_source_action.setEnabled(True)
            self.auto_import_action.setEnabled(True)
        else:
            # Editor
            self.combo.hide()
            self.object_edit.show()
            self.show_source_action.setDisabled(True)
            self.auto_import_action.setDisabled(True)
        self.restore_text()
            
    def save_text(self, callback):
        if self.source_is_console():
            self._last_console_cb = callback
        else:
            self._last_editor_cb = callback
            
    def restore_text(self):
        if self.source_is_console():
            cb = self._last_console_cb
        else:
            cb = self._last_editor_cb
        if cb is None:
            if self.is_plain_text_mode():
                self.plain_text.clear()
            else:
                self.rich_text.clear()
        else:
            func = cb[0]
            args = cb[1:]
            func(*args)
            if func.im_self is self.rich_text:
                self.switch_to_rich_text()
            else:
                self.switch_to_plain_text()
        
    #------ Public API (related to rich/plain text widgets) --------------------
    @property
    def find_widget(self):
        if self.plain_text.isVisible():
            return self.plain_text.find_widget
        else:
            return self.rich_text.find_widget
    
    def set_rich_text_font(self, font):
        """Set rich text mode font"""
        self.rich_text.set_font(font, fixed_font=self.get_plugin_font())
        
    def set_plain_text_font(self, font, color_scheme=None):
        """Set plain text mode font"""
        self.plain_text.set_font(font, color_scheme=color_scheme)

    def set_plain_text_color_scheme(self, color_scheme):
        """Set plain text mode color scheme"""
        self.plain_text.set_color_scheme(color_scheme)
        
    def change_font(self):
        """Change console font"""
        font, valid = QFontDialog.getFont(get_font(self.CONF_SECTION), self,
                                      _("Select a new font"))
        if valid:
            self.set_plain_text_font(font)
            set_font(font, self.CONF_SECTION)
            
    def toggle_wrap_mode(self, checked):
        """Toggle wrap mode"""
        self.plain_text.editor.toggle_wrap_mode(checked)
        self.set_option('wrap', checked)
    
    def toggle_math_mode(self, checked):
        """Toggle math mode"""
        self.set_option('math', checked)
    
    def is_plain_text_mode(self):
        """Return True if plain text mode is active"""
        return self.plain_text.isVisible()

    def is_rich_text_mode(self):
        """Return True if rich text mode is active"""
        return self.rich_text.isVisible()

    def switch_to_plain_text(self):
        """Switch to plain text mode"""
        self.rich_help = False
        self.plain_text.show()
        self.rich_text.hide()
        self.plain_text_action.setChecked(True)
        
    def switch_to_rich_text(self):
        """Switch to rich text mode"""
        self.rich_help = True
        self.plain_text.hide()
        self.rich_text.show()
        self.rich_text_action.setChecked(True)
        self.show_source_action.setChecked(False)
            
    def set_plain_text(self, text, is_code):
        """Set plain text docs"""
        
        # text is coming from utils.dochelpers.getdoc
        if type(text) is dict:
            name = text['name']
            if name:
                rst_title = ''.join(['='*len(name), '\n', name, '\n',
                                    '='*len(name), '\n\n'])
            else:
                rst_title = ''
            
            if text['argspec']:
                definition = ''.join(['Definition: ', name, text['argspec'],
                                      '\n'])
            else:
                definition = ''
            
            if text['note']:
                note = ''.join(['Type: ', text['note'], '\n\n----\n\n'])
            else:
                note = ''

            full_text = ''.join([rst_title, definition, note,
                                 text['docstring']])
        else:
            full_text = text
        
        self.plain_text.set_text(full_text, is_code)
        self.save_text([self.plain_text.set_text, full_text, is_code])
        
    def set_rich_text_html(self, html_text, base_url):
        """Set rich text"""
        self.rich_text.set_html(html_text, base_url)
        self.save_text([self.rich_text.set_html, html_text, base_url])
        
    #------ Public API ---------------------------------------------------------
    def set_external_console(self, external_console):
        self.external_console = external_console
    
    def force_refresh(self):
        if self.source_is_console():
            self.set_object_text(None, force_refresh=True)
        elif self._last_rope_data is not None:
            text = self._last_rope_data
            self.set_rope_doc(text, force_refresh=True)
    
    def set_object_text(self, text, force_refresh=False, ignore_unknown=False):
        """Set object analyzed by Object Inspector"""
        if (self.locked and not force_refresh):
            return

        self.switch_to_console_source()

        add_to_combo = True
        if text is None:
            text = unicode(self.combo.currentText())
            add_to_combo = False
            
        found = self.show_help(text, ignore_unknown=ignore_unknown)
        if ignore_unknown and not found:
            return
        
        if add_to_combo:
            self.combo.add_text(text)
        self.save_history()
        
        if self.dockwidget is not None:
            self.dockwidget.blockSignals(True)
        self.__eventually_raise_inspector(text, force=force_refresh)
        if self.dockwidget is not None:
            self.dockwidget.blockSignals(False)
        
    def set_rope_doc(self, text, force_refresh=False):
        """
        Use the object inspector to show text computed with rope from the
        Editor plugin
        """
        if (self.locked and not force_refresh):
            return
        self.switch_to_editor_source()
        
        self._last_rope_data = text
        
        self.object_edit.setText(text['obj_text'])
        
        if self.rich_help:
            self.set_sphinx_text(text)
        else:
            self.set_plain_text(text, is_code=False)
        
        if self.dockwidget is not None:
            self.dockwidget.blockSignals(True)
        self.__eventually_raise_inspector(text['docstring'],
                                          force=force_refresh)
        if self.dockwidget is not None:
            self.dockwidget.blockSignals(False)
            
    def __eventually_raise_inspector(self, text, force=False):
        index = self.source_combo.currentIndex()
        if hasattr(self.main, 'tabifiedDockWidgets'):
            # 'QMainWindow.tabifiedDockWidgets' was introduced in PyQt 4.5
            if self.dockwidget and (force or self.dockwidget.isVisible()) \
               and not self.ismaximized \
               and (force or text != self._last_texts[index]):
                dockwidgets = self.main.tabifiedDockWidgets(self.dockwidget)
                if self.main.console.dockwidget not in dockwidgets and \
                   (hasattr(self.main, 'extconsole') and \
                    self.main.extconsole.dockwidget not in dockwidgets):
                    self.dockwidget.show()
                    self.dockwidget.raise_()
        self._last_texts[index] = text
    
    def load_history(self, obj=None):
        """Load history from a text file in user home directory"""
        if osp.isfile(self.LOG_PATH):
            history = [line.replace('\n','')
                       for line in file(self.LOG_PATH, 'r').readlines()]
        else:
            history = []
        return history
    
    def save_history(self):
        """Save history to a text file in user home directory"""
        file(self.LOG_PATH, 'w').write("\n".join( \
            [ unicode( self.combo.itemText(index) )
                for index in range(self.combo.count()) ] ))
        
    def toggle_plain_text(self, checked):
        """Toggle plain text docstring"""
        if checked:
            self.docstring = checked
            self.switch_to_plain_text()
            self.force_refresh()
        self.set_option('rich_mode', not checked)
        
    def toggle_show_source(self, checked):
        """Toggle show source code"""
        if checked:
            self.switch_to_plain_text()
        self.docstring = not checked
        self.force_refresh()
        self.set_option('rich_mode', not checked)
        
    def toggle_rich_text(self, checked):
        """Toggle between sphinxified docstrings or plain ones"""
        if checked:
            self.docstring = not checked
            self.switch_to_rich_text()
            self.force_refresh()
        self.set_option('rich_mode', checked)
        
    def toggle_auto_import(self, checked):
        """Toggle automatic import feature"""
        self.combo.validate_current_text()
        self.set_option('automatic_import', checked)
        self.force_refresh()
        
    def toggle_locked(self):
        """
        Toggle locked state
        locked = disable link with Console
        """
        self.locked = not self.locked
        self._update_lock_icon()
        
    def _update_lock_icon(self):
        """Update locked state icon"""
        icon = get_icon("lock.png" if self.locked else "lock_open.png")
        self.locked_button.setIcon(icon)
        tip = _("Unlock") if self.locked else _("Lock")
        self.locked_button.setToolTip(tip)
        
    def set_shell(self, shell):
        """Bind to shell"""
        if IPythonControlWidget is not None:
            # XXX(anatoli): hack to make Spyder run on systems without IPython
            #               there should be a better way
            if isinstance(shell, IPythonControlWidget):
                # XXX: this ignores passed argument completely
                self.shell = self.external_console.get_current_shell()
        else:
            self.shell = shell
    
    def get_shell(self):
        """Return shell which is currently bound to object inspector,
        or another running shell if it has been terminated"""
        if not isinstance(self.shell, ExtPythonShellWidget) \
           or not self.shell.externalshell.is_running():
            self.shell = None
            if self.external_console is not None:
                self.shell = self.external_console.get_running_python_shell()
            if self.shell is None:
                self.shell = self.internal_shell
        return self.shell
        
    def set_sphinx_text(self, text):
        """Sphinxify text and display it"""
        # If the thread is already running wait for it to finish before
        # starting it again.
        if self._sphinx_thread.wait():
            # Math rendering option could have changed
            self._sphinx_thread.math_option = self.get_option('math')
            self._sphinx_thread.text = text
            self._sphinx_thread.start()
        
    def _on_sphinx_thread_html_ready(self, html_text):
        """Set our sphinx documentation based on thread result"""
        self.set_rich_text_html(html_text, QUrl.fromLocalFile(CSS_PATH))

    def _on_sphinx_thread_error_msg(self, error_msg):
        """ Display error message on Sphinx rich text failure"""
        self.plain_text_action.setChecked(True)
        QMessageBox.critical(self,
                    _('Object inspector'),
                    _("The following error occured when calling "
                      "<b>Sphinx %s</b>. <br>Incompatible Sphinx "
                      "version or doc string decoding failed."
                      "<br><br>Error message:<br>%s"
                      ) % (sphinx_version, error_msg))

    def show_help(self, obj_text, ignore_unknown=False):
        """Show help"""
        shell = self.get_shell()
        if shell is None:
            return
        obj_text = unicode(obj_text)
        
        if not shell.is_defined(obj_text):
            if self.get_option('automatic_import') and\
               self.internal_shell.is_defined(obj_text, force_import=True):
                shell = self.internal_shell
            else:
                shell = None
                doc_text = None
                source_text = None
            
        if shell is not None:
            doc_text = shell.get_doc(obj_text)
            if isinstance(doc_text, bool):
                doc_text = None
            source_text = shell.get_source(obj_text)
            
        is_code = False
        
        if self.rich_help:
            self.set_sphinx_text(doc_text)
            if ignore_unknown:
                return doc_text is not None
            else:
                return True
        
        elif self.docstring:
            hlp_text = doc_text
            if hlp_text is None:
                hlp_text = source_text
                if hlp_text is None:
                    hlp_text = self.no_doc_string
                    if ignore_unknown:
                        return False
        else:
            hlp_text = source_text
            if hlp_text is None:
                hlp_text = doc_text
                if hlp_text is None:
                    hlp_text = _("No source code available.")
                    if ignore_unknown:
                        return False
            else:
                is_code = True
        
        self.set_plain_text(hlp_text, is_code=is_code)
        return True
