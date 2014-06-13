# -*- coding: utf-8 -*-
#
# Copyright © 2014-2014 Shi Senjia 
# Licensed under the terms of the MIT License
# (see SMlib/__init__.py for details)

"""
Dictionary Editor Tree Widget based on Qt
"""

from PyQt4.QtCore import (Qt, QAbstractItemModel, QModelIndex,
                          SIGNAL,SLOT, QDateTime, pyqtSignal)
from PyQt4.QtGui import ( QStandardItemModel,QStandardItem, QTreeView, QMessageBox, QItemDelegate,
                                QLineEdit, QVBoxLayout, QWidget, QColor,
                                QDialog, QDateEdit, QDialogButtonBox, QMenu,
                                QInputDialog, QDateTimeEdit, QApplication,
                                QKeySequence)

import os
import sys
import datetime

# Local import
from SMlib.configs.baseconfig import _
from SMlib.configs.guiconfig import get_font
from SMlib.utils.misc import fix_reference_name
from SMlib.utils.qthelpers import (get_icon, add_actions, create_action,
                                       qapplication,to_qvariant, from_qvariant, getsavefilename)
from SMlib.widgets.dicteditorutils import (sort_against, get_size,
               get_human_readable_type, value_to_display, get_color_name,
               is_known_type, FakeObject, Image, ndarray, array, MaskedArray,
               unsorted_unique, try_to_eval, datestr_to_datetime,
               get_numpy_dtype, is_editable_type)
from SMlib.widgets.importwizard import ImportWizard
if ndarray is not FakeObject:
    from SMlib.widgets.arrayeditor import ArrayEditor
from SMlib.widgets.texteditor import TextEditor
from SMlib.widgets.dicteditor import (display_to_value, DictEditor)

class ProxyObject(object):
    """Dictionary proxy to an unknown object"""
    def __init__(self, obj):
        self.__obj__ = obj
    
    def __len__(self):
        return len(dir(self.__obj__))
    
    def __getitem__(self, key):
        return getattr(self.__obj__, key)
    
    def __setitem__(self, key, value):
        setattr(self.__obj__, key, value)
        
class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = TreeItem(data, self)
            self.childItems.insert(position, item)

        return True

    def insertColumns(self, position, columns):
        if position < 0 or position > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.insert(position, None)

        for child in self.childItems:
            child.insertColumns(position, columns)

        return True

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def removeColumns(self, position, columns):
        if position < 0 or position + columns > len(self.itemData):
            return False

        for column in range(columns):
            self.itemData.pop(position)

        for child in self.childItems:
            child.removeColumns(position, columns)

        return True

    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False
        self.itemData[column] = value
        return True


class ReadOnlyTreeModel(QAbstractItemModel):
    def __init__(self, parent, data, title="", names=False,
                 truncate=True, minmax=False, collvalue=True, remote=False):
        super(ReadOnlyTreeModel, self).__init__(parent)
        
        self.names = names
        self.truncate = truncate
        self.minmax = minmax
        self.collvalue = collvalue
        self.remote = remote
        rootData = [_("name"), _("type"), _("size"), _("view")]
        
        self.rootItem = TreeItem(rootData)
        self.data = None
        
        self.title = unicode(title) # in case title is not a string
        if self.title:
            self.title = self.title + ' - '

        self.set_data(data)
        
    def get_data(self):
        return self.data
    
    def columnCount(self, parent=QModelIndex()):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None
        
        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None
        
        item = self.getItem(index)
        value = item.data(index.column())
        
        display = value_to_display(value,
                               truncate=index.column() == 3 and self.truncate,
                               minmax=self.minmax,
                               collvalue=self.collvalue or index.column() != 3)
        if role == Qt.DisplayRole:
            return to_qvariant(display)
        elif role == Qt.EditRole:
            return to_qvariant(value_to_display(value))
        elif role == Qt.TextAlignmentRole:
            if index.column() == 3:
                if len(display.splitlines()) < 3:
                    return to_qvariant(int(Qt.AlignLeft|Qt.AlignVCenter))
                else:
                    return to_qvariant(int(Qt.AlignLeft|Qt.AlignTop))
            else:
                return to_qvariant(int(Qt.AlignLeft|Qt.AlignVCenter))
        elif role == Qt.BackgroundColorRole:
            print index.row(), index.column()
            return to_qvariant( self.get_bgcolor(index) )
        elif role == Qt.FontRole:
            if index.column() < 3:
                return to_qvariant(get_font('dicteditor_header'))
            else:
                return to_qvariant(get_font('dicteditor'))
            


    def flags(self, index):
        if not index.isValid():
            return 0

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def headerData(self, section, orientation, role= Qt.DisplayRole):
        if role != Qt.DisplayRole:
            if role == Qt.FontRole:
                return to_qvariant(get_font('dicteditor_header'))
            else:
                return to_qvariant()
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def insertColumns(self, position, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        success = self.rootItem.insertColumns(position, columns)
        self.endInsertColumns()

        return success

    def insertRows(self, position, rows, parent=QModelIndex()):
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parentItem.insertChildren(position, rows,
                self.rootItem.columnCount())
        self.endInsertRows()

        return success

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def removeColumns(self, position, columns, parent=QModelIndex()):
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success = self.rootItem.removeColumns(position, columns)
        self.endRemoveColumns()

        if self.rootItem.columnCount() == 0:
            self.removeRows(0, self.rowCount())

        return success

    def removeRows(self, position, rows, parent=QModelIndex()):
        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parentItem.removeChildren(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent=QModelIndex()):
        parentItem = self.getItem(parent)

        return parentItem.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role != Qt.EditRole or orientation != Qt.Horizontal:
            return False

        result = self.rootItem.setData(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def set_data(self, data, dictfilter=None):
        self.data = data
        if dictfilter is not None and not self.remote and\
           isinstance(data, (tuple, list, dict)):
            data = dictfilter(data)
        
        self.showndata = data
        parent = self.rootItem
        self.rootItem.removeChildren(0, self.rootItem.childCount())

        if data:
            for index in data:
                pre_parent = self._appendRow(parent, index, data[index]['type'], str(data[index]["size"]), 
                                data[index]["view"])
                if data[index]['type'] == "dict" or data[index]['type'] == "list":
                    self._appendChildRow(pre_parent, data[index]['value'])
            

        self.reset()
    
    ##
    def get_bgcolor(self, index):
        """Background color depending on value"""
        if index.column() == 0:
            color = QColor(Qt.lightGray)
            color.setAlphaF(.05)
        elif index.column() < 3:
            color = QColor(Qt.lightGray)
            color.setAlphaF(.2)
        else:
            color = QColor(Qt.lightGray)
            color.setAlphaF(.3)
        return color
    #
    def get_value(self, index):
        if index.column() == 3 :
            return self._getView(index)
        else:
            return self.getItem(index).data(index.column())
        
    def _getView(self, index):
        
        item = self.getItem(index)
        parent = item.parent()
        
        parentList = [item]
        while parent != self.rootItem:
            parentList.append(parent)
            parent = parent.parent()
            
        root = parentList.pop()
        data = self.get_data().get(root.data(0)).get('value')
        
        name = root.data(0)
        
        return self._get_data(parentList, data)
    
    def get_key(self, index):
        return self.getItem(index).data(0)
        
    #========================private function ================================================#
    def _get_data(self, parentList, data):
        while len(parentList) != 0:
            parent = parentList.pop()
            if isinstance(data, dict):
                data = data.get(parent.data(0))
            elif isinstance(data,(int, str, float)):
                data = data
            elif isinstance(data, (tuple, list)):
                data = data[int(parent.data(0)[1:-1])]
        return data
    
    def _appendChildRow(self, parent, datas):
        
        if isinstance(datas, dict):
            for index in datas:
                value = datas[index]
                display = value_to_display(value, truncate= self.truncate, 
                                           minmax=self.minmax, collvalue=self.collvalue )
                pre_parent = self._appendRow(parent, index, get_human_readable_type(value),
                                             get_size(value), display)
                if isinstance(value, (dict, list, tuple)):
                    self._appendChildRow(pre_parent, value)
        elif isinstance(datas, (list, tuple)):
            for index in range(len(datas)):
                value = datas[index]
                display = value_to_display(value, truncate= self.truncate, 
                                           minmax=self.minmax, collvalue=self.collvalue )
                pre_parent = self._appendRow(parent, '[%d]' % index, get_human_readable_type(value),
                                             get_size(value), display)
                if isinstance(value, (dict, list, tuple)):
                    self._appendChildRow(pre_parent, value)
    
    def _appendRow(self, parent, _name, _type, _size, _view):
        parent.insertChildren(parent.childCount(), 1, self.rootItem.columnCount())
        item = parent.child(parent.childCount() - 1)
        item.setData(0, _name)
        item.setData(1, _type)
        item.setData(2, _size)
        item.setData(3, _view)
        
        return item
    #========================private function ================================================#
    
class DictModel(ReadOnlyTreeModel):
    """DictEditor Tree Model"""
    
    def set_value(self, index, value):
        """Set value"""
        
        item = self.getItem(index)
        parent = item.parent()
        self.getItem(index).setData(3, value)
        parentList = [self.getItem(index)]
        while parent != self.rootItem:
            parentList.append(parent)
            parent = parent.parent()
        
        source = self.get_data().get(parentList[-1].data(0)).get('value')
        root = parentList.pop()
        name = root.data(0)

        if isinstance(source, dict):
            newData = self._toData(value, parentList, source)
        elif isinstance(source, (int, float, str)):
            newData = value
        
        self.set_value_func(name, newData)
        #self.get_data()[parent.data(0)]
    def _toData(self, value, parentList, data):
        def update(value, parent, data):
            newData = data
            if isinstance(newData, dict):
                dValue = {parent.data(0): value}
                newData.update(dValue)
            elif isinstance(newData, (list, tuple)):
                newData[int(parent.data(0)[1:-1])] = value
            elif isinstance(newData, (int, float, str)):
                newData = value
            return newData
        
        def getChildData(child, data):
            if isinstance(data, dict):
                return data.get(child.data(0))
            elif isinstance(data, (list, tuple)):
                ch = child.data(0)[1:-1]
                return data[int(ch)]
            else:
                return data
            
        if len(parentList) == 1:
            p = parentList.pop()
            newData = update(value, p, data)
            return newData
        else :
            p = parentList.pop()
            child = getChildData(p, data)
            newData = update(value, p, self._toData(value, parentList, child))
            return newData
        
    def get_bgcolor(self, index):
        """Background color depending on value"""
        value = self.get_value(index)
        if index.column() < 3:
            color = ReadOnlyTreeModel.get_bgcolor(self, index)
        else:
            if self.remote:
                color_name = value['color']
            else:
                color_name = get_color_name(value)
            color = QColor(color_name)
            color.setAlphaF(.2)
        return color
    
class BaseTreeView(QTreeView):
    """Base dictionnary editor table view"""
    sig_option_changed = pyqtSignal(str, object)
    def __init__(self, parent):
        QTreeView.__init__(self, parent)
        self.array_filename = None
        self.menu = None
        self.empty_ws_menu = None
        self.paste_action = None
        self.copy_action = None
        self.edit_action = None
        self.plot_action = None
        self.hist_action = None
        self.imshow_action = None
        self.save_array_action = None
        self.insert_action = None
        self.remove_action = None
        self.truncate_action = None
        self.minmax_action = None
        self.collvalue_action = None
        self.inplace_action = None
        self.rename_action = None
        self.duplicate_action = None
        self.delegate = None
        
    def setup_table(self):
        """Setup table"""
        self.header().setStretchLastSection(True)
        self.adjust_columns()
        # Sorting columns
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        
    def setup_menu(self, truncate, minmax, inplace, collvalue):
        """Setup context menu"""
        if self.truncate_action is not None:
            self.truncate_action.setChecked(truncate)
            self.minmax_action.setChecked(minmax)
            self.inplace_action.setChecked(inplace)
            self.collvalue_action.setChecked(collvalue)
            return
        
        #resize_action = create_action(self, _("Resize rows to contents"),
        #                              triggered=self.resizeRowsToContents)
        resize_action = None
        self.paste_action = create_action(self, _("Paste"),
                                          icon=get_icon('editpaste.png'),
                                          triggered=self.paste)
        self.copy_action = create_action(self, _("Copy"),
                                         icon=get_icon('editcopy.png'),
                                         triggered=self.copy)                                      
        self.edit_action = create_action(self, _("Edit"),
                                         icon=get_icon('edit.png'),
                                         triggered=self.edit_item)
        self.plot_action = create_action(self, _("Plot"),
                                    icon=get_icon('plot.png'),
                                    triggered=lambda: self.plot_item('plot'))
        self.plot_action.setVisible(False)
        self.hist_action = create_action(self, _("Histogram"),
                                    icon=get_icon('hist.png'),
                                    triggered=lambda: self.plot_item('hist'))
        self.hist_action.setVisible(False)
        self.imshow_action = create_action(self, _("Show image"),
                                           icon=get_icon('imshow.png'),
                                           triggered=self.imshow_item)
        self.imshow_action.setVisible(False)
        self.save_array_action = create_action(self, _("Save array"),
                                               icon=get_icon('filesave.png'),
                                               triggered=self.save_array)
        self.save_array_action.setVisible(False)
        self.insert_action = create_action(self, _("Insert"),
                                           icon=get_icon('insert.png'),
                                           triggered=self.insert_item)
        self.remove_action = create_action(self, _("Remove"),
                                           icon=get_icon('editdelete.png'),
                                           triggered=self.remove_item)
        self.truncate_action = create_action(self, _("Truncate values"),
                                             toggled=self.toggle_truncate)
        self.truncate_action.setChecked(truncate)
        self.toggle_truncate(truncate)
        self.minmax_action = create_action(self, _("Show arrays min/max"),
                                           toggled=self.toggle_minmax)
        self.minmax_action.setChecked(minmax)
        self.toggle_minmax(minmax)
        self.collvalue_action = create_action(self,
                                              _("Show collection contents"),
                                              toggled=self.toggle_collvalue)
        self.collvalue_action.setChecked(collvalue)
        self.toggle_collvalue(collvalue)
        self.inplace_action = create_action(self, _("Always edit in-place"),
                                            toggled=self.toggle_inplace)
        self.inplace_action.setChecked(inplace)
        if self.delegate is None:
            self.inplace_action.setEnabled(False)
        else:
            self.toggle_inplace(inplace)
        self.rename_action = create_action(self, _( "Rename"),
                                           icon=get_icon('rename.png'),
                                           triggered=self.rename_item)
        self.duplicate_action = create_action(self, _( "Duplicate"),
                                              icon=get_icon('edit_add.png'),
                                              triggered=self.duplicate_item)
        menu = QMenu(self)
        menu_actions = [self.edit_action, self.plot_action, self.hist_action,
                        self.imshow_action, self.save_array_action,
                        self.insert_action, self.remove_action,
                        self.copy_action, self.paste_action,
                        None, self.rename_action,self.duplicate_action,
                        None, resize_action, None, self.truncate_action,
                        self.inplace_action, self.collvalue_action]
        if ndarray is not FakeObject:
            menu_actions.append(self.minmax_action)
        add_actions(menu, menu_actions)
        self.empty_ws_menu = QMenu(self)
        add_actions(self.empty_ws_menu,
                    [self.insert_action, self.paste_action,
                     None, resize_action])
        return menu
    
    #------ Remote/local API ---------------------------------------------------
    def remove_values(self, keys):
        """Remove values from data"""
        raise NotImplementedError

    def copy_value(self, orig_key, new_key):
        """Copy value"""
        raise NotImplementedError
    
    def new_value(self, key, value):
        """Create new value in data"""
        raise NotImplementedError
        
    def is_list(self, key):
        """Return True if variable is a list or a tuple"""
        raise NotImplementedError
        
    def get_len(self, key):
        """Return sequence length"""
        raise NotImplementedError
        
    def is_array(self, key):
        """Return True if variable is a numpy array"""
        raise NotImplementedError

    def is_image(self, key):
        """Return True if variable is a PIL.Image image"""
        raise NotImplementedError
    
    def is_dict(self, key):
        """Return True if variable is a dictionary"""
        raise NotImplementedError
        
    def get_array_shape(self, key):
        """Return array's shape"""
        raise NotImplementedError
        
    def get_array_ndim(self, key):
        """Return array's ndim"""
        raise NotImplementedError
    
    def oedit(self, key):
        """Edit item"""
        raise NotImplementedError
    
    def plot(self, key, funcname):
        """Plot item"""
        raise NotImplementedError
    
    def imshow(self, key):
        """Show item's image"""
        raise NotImplementedError
    
    def show_image(self, key):
        """Show image (item is a PIL image)"""
        raise NotImplementedError
    #---------------------------------------------------------------------------
            
    def refresh_menu(self):
        """Refresh context menu"""
        index = self.currentIndex()
        condition = index.isValid()
        self.edit_action.setEnabled( condition )
        self.remove_action.setEnabled( condition )
        #self.refresh_plot_entries(index)
        
    def refresh_plot_entries(self, index):
        if index.isValid():
            key = self.model.getItem(index)
            is_list = self.is_list(key)
            is_array = self.is_array(key) and self.get_len(key) != 0
            condition_plot = (is_array and len(self.get_array_shape(key)) <= 2)
            condition_hist = (is_array and self.get_array_ndim(key) == 1)
            condition_imshow = condition_plot and self.get_array_ndim(key) == 2
            condition_imshow = condition_imshow or self.is_image(key)
        else:
            is_array = condition_plot = condition_imshow = is_list \
                     = condition_hist = False
        self.plot_action.setVisible(condition_plot or is_list)
        self.hist_action.setVisible(condition_hist or is_list)
        self.imshow_action.setVisible(condition_imshow)
        self.save_array_action.setVisible(is_array)
        
    def adjust_columns(self):
        """Resize two first columns to contents"""
        for col in range(3):
            self.resizeColumnToContents(col)
        
    def set_data(self, data):
        """Set table data"""
        if data is not None:
            self.model.set_data(data, self.dictfilter)
            #self.sortByColumn(0, Qt.AscendingOrder)

    def mousePressEvent(self, event):
        """Reimplement Qt method"""
        if event.button() != Qt.LeftButton:
            QTreeView.mousePressEvent(self, event)
            return
        index_clicked = self.indexAt(event.pos())
        if index_clicked.isValid():
            if index_clicked == self.currentIndex() \
               and index_clicked in self.selectedIndexes():
                self.clearSelection()
            else:
                QTreeView.mousePressEvent(self, event)
        else:
            self.clearSelection()
            event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Reimplement Qt method"""
        index_clicked = self.indexAt(event.pos())
        if index_clicked.isValid():
            self.edit_item()
        else:
            event.accept()
    
    def keyPressEvent(self, event):
        """Reimplement Qt methods"""
        if event.key() == Qt.Key_Delete:
            self.remove_item()
        elif event.key() == Qt.Key_F2:
            self.rename_item()
        elif event == QKeySequence.Copy:
            self.copy()
        elif event == QKeySequence.Paste:
            self.paste()
        else:
            QTreeView.keyPressEvent(self, event)
        
    def contextMenuEvent(self, event):
        """Reimplement Qt method"""
        if self.model.showndata:
            self.refresh_menu()
            self.menu.popup(event.globalPos())
            event.accept()
        else:
            self.empty_ws_menu.popup(event.globalPos())
            event.accept()

    def toggle_inplace(self, state):
        """Toggle in-place editor option"""
        self.sig_option_changed.emit('inplace', state)
        self.delegate.inplace = state
        
    def toggle_truncate(self, state):
        """Toggle display truncating option"""
        self.sig_option_changed.emit('truncate', state)
        self.model.truncate = state
        
    def toggle_minmax(self, state):
        """Toggle min/max display for numpy arrays"""
        self.sig_option_changed.emit('minmax', state)
        self.model.minmax = state
        
    def toggle_collvalue(self, state):
        """Toggle value display for collections"""
        self.sig_option_changed.emit('collvalue', state)
        self.model.collvalue = state
            
    def edit_item(self):
        """Edit item"""
        index = self.currentIndex()
        if not index.isValid():
            return
        self.edit(index)
    
    def remove_item(self):
        """Remove item"""
        """Bug: These is a bug of selection. We needs to select single item"""
        indexes = self.selectedIndexes()
        if not indexes:
            return
        for index in indexes:
            if not index.isValid():
                return
        one = _("Do you want to remove selected item?")
        more = _("Do you want to remove all selected items?")
        answer = QMessageBox.question(self, _( "Remove"),
                                      one if len(indexes) == 1 else more,
                                      QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            #idx_rows = unsorted_unique(map(lambda idx: idx.row(), indexes))
            #keys = [ self.model.keys[idx_row] for idx_row in idx_rows ]
            keys = [ self.model.get_key(idx) for idx in indexes]
            self.remove_values(keys)

    def copy_item(self, erase_original=False):
        """Copy item"""
        indexes = self.selectedIndexes()
        if not indexes:
            return
        idx_rows = unsorted_unique(map(lambda idx: idx.row(), indexes))
        if len(idx_rows) > 1 or not indexes[0].isValid():
            return
        orig_key = self.model.keys[idx_rows[0]]
        new_key, valid = QInputDialog.getText(self, _( 'Rename'), _( 'Key:'),
                                              QLineEdit.Normal,orig_key)
        if valid and unicode(new_key):
            new_key = try_to_eval(unicode(new_key))
            if new_key == orig_key:
                return
            self.copy_value(orig_key, new_key)
            if erase_original:
                self.remove_values([orig_key])
    
    def duplicate_item(self):
        """Duplicate item"""
        self.copy_item()

    def rename_item(self):
        """Rename item"""
        self.copy_item(True)
    
    def insert_item(self):
        """Insert item"""
        index = self.currentIndex()
        if not index.isValid():
            row = self.model.rowCount()
        else:
            row = index.row()
        data = self.model.get_data()
        if isinstance(data, list):
            key = row
            data.insert(row, '')
        elif isinstance(data, dict):
            key, valid = QInputDialog.getText(self, _( 'Insert'), _( 'Key:'),
                                              QLineEdit.Normal)
            if valid and unicode(key):
                key = try_to_eval(unicode(key))
            else:
                return
        else:
            return
        value, valid = QInputDialog.getText(self, _('Insert'), _('Value:'),
                                            QLineEdit.Normal)
        if valid and unicode(value):
            self.new_value(key, try_to_eval(unicode(value)))
            
    def __prepare_plot(self):
        try:
            import guiqwt.pyplot #analysis:ignore
            return True
        except ImportError:
            try:
                if 'matplotlib' not in sys.modules:
                    import matplotlib
                    matplotlib.use("Qt4Agg")
                return True
            except ImportError:
                QMessageBox.warning(self, _("Import error"),
                                    _("Please install <b>matplotlib</b>"
                                      " or <b>guiqwt</b>."))

    def plot_item(self, funcname):
        """Plot item"""
        index = self.currentIndex()
        if self.__prepare_plot():
            key = self.model.getItem(index)
            try:
                self.plot(key, funcname)
            except (ValueError, TypeError), error:
                QMessageBox.critical(self, _( "Plot"),
                                     _("<b>Unable to plot data.</b>"
                                       "<br><br>Error message:<br>%s"
                                       ) % str(error))
            
    def imshow_item(self):
        """Imshow item"""
        index = self.currentIndex()
        if self.__prepare_plot():
            key = self.model.getItem(index)
            try:
                if self.is_image(key):
                    self.show_image(key)
                else:
                    self.imshow(key)
            except (ValueError, TypeError), error:
                QMessageBox.critical(self, _( "Plot"),
                                     _("<b>Unable to show image.</b>"
                                       "<br><br>Error message:<br>%s"
                                       ) % str(error))
            
    def save_array(self):
        """Save array"""
        title = _( "Save array")
        if self.array_filename is None:
            self.array_filename = os.getcwdu()
        self.emit(SIGNAL('redirect_stdio(bool)'), False)
        filename, _selfilter = getsavefilename(self, title,
                                               self.array_filename,
                                               _("NumPy arrays")+" (*.npy)")
        self.emit(SIGNAL('redirect_stdio(bool)'), True)
        if filename:
            self.array_filename = filename
            data = self.delegate.get_value( self.currentIndex() )
            try:
                import numpy as np
                np.save(self.array_filename, data)
            except Exception, error:
                QMessageBox.critical(self, title,
                                     _("<b>Unable to save array</b>"
                                       "<br><br>Error message:<br>%s"
                                       ) % str(error))
    def copy(self):
        """Copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipl = []
        index = self.currentIndex()
        if index.isValid():
            clipl.append(unicode(self.delegate.get_value(index)))
        clipboard.setText(u'\n'.join(clipl))
    
    def import_from_string(self, text, title=None):
        """Import data from string"""
        data = self.model.get_data()
        editor = ImportWizard(self, text, title=title,
                              contents_title=_("Clipboard contents"),
                              varname=fix_reference_name("data",
                                                         blacklist=data.keys()))
        if editor.exec_():
            var_name, clip_data = editor.get_data()
            self.new_value(var_name, clip_data)
    
    def paste(self):
        """Import text/data/code from clipboard"""
        clipboard = QApplication.clipboard()
        cliptext = u""
        if clipboard.mimeData().hasText():
            cliptext = unicode(clipboard.text())
        if cliptext.strip():
            self.import_from_string(cliptext, title=_("Import from clipboard"))
        else:
            QMessageBox.warning(self, _( "Empty clipboard"),
                                _("Nothing to be imported from clipboard."))
            


class DictDelegate(QItemDelegate):
    """DictEditor Item Delegate"""
    def __init__(self, parent=None, inplace=False):
        QItemDelegate.__init__(self, parent)
        self.inplace = inplace
        self._editors = {} # keep references on opened editors
        
    def get_value(self, index):
        if index.isValid():
            return index.model().get_value(index)
    
    def set_value(self, index, value):
        if index.isValid():
            index.model().set_value(index, value)

    def createEditor(self, parent, option, index):
        """Overriding method createEditor"""
        if index.column() < 3:
            return None
        try:
            value = self.get_value(index)
        except Exception, msg:
            QMessageBox.critical(self.parent(), _("Edit item"),
                                 _("<b>Unable to retrieve data.</b>"
                                   "<br><br>Error message:<br>%s"
                                   ) % unicode(msg))
            return
        key = index.model().get_key(index)
        readonly = isinstance(value, tuple) or self.parent().readonly \
                   or not is_known_type(value)
        #---editor = DictEditor
        if isinstance(value, (list, tuple, dict)) and not self.inplace:
            editor = DictEditor()
            editor.setup(value, key, icon=self.parent().windowIcon(),
                         readonly=readonly)
            self.create_dialog(editor, dict(model=index.model(), editor=editor,
                                            key=key, readonly=readonly))
            return None
        #---editor = ArrayEditor
        elif isinstance(value, (ndarray, MaskedArray))\
             and ndarray is not FakeObject and not self.inplace:
            if value.size == 0:
                return None
            editor = ArrayEditor(parent)
            if not editor.setup_and_check(value, title=key, readonly=readonly):
                return
            self.create_dialog(editor, dict(model=index.model(), editor=editor,
                                            key=key, readonly=readonly))
            return None
        #---showing image
        elif isinstance(value, Image) and ndarray is not FakeObject \
             and Image is not FakeObject:
            arr = array(value)
            if arr.size == 0:
                return None
            editor = ArrayEditor(parent)
            if not editor.setup_and_check(arr, title=key, readonly=readonly):
                return
            conv_func = lambda arr: Image.fromarray(arr, mode=value.mode)
            self.create_dialog(editor, dict(model=index.model(), editor=editor,
                                            key=key, readonly=readonly,
                                            conv=conv_func))
            return None
        #---editor = QDateTimeEdit
        elif isinstance(value, datetime.datetime) and not self.inplace:
            editor = QDateTimeEdit(value, parent)
            editor.setCalendarPopup(True)
            editor.setFont(get_font('dicteditor'))
            self.connect(editor, SIGNAL("returnPressed()"),
                         self.commitAndCloseEditor)
            return editor
        #---editor = QDateEdit
        elif isinstance(value, datetime.date) and not self.inplace:
            editor = QDateEdit(value, parent)
            editor.setCalendarPopup(True)
            editor.setFont(get_font('dicteditor'))
            self.connect(editor, SIGNAL("returnPressed()"),
                         self.commitAndCloseEditor)
            return editor
        #---editor = QTextEdit
        elif isinstance(value, (str, unicode)) and len(value)>40:
            editor = TextEditor(value, key)
            self.create_dialog(editor, dict(model=index.model(), editor=editor,
                                            key=key, readonly=readonly))
            return None
        #---editor = QLineEdit
        elif self.inplace or is_editable_type(value):
            editor = QLineEdit(parent)
            editor.setFont(get_font('dicteditor'))
            editor.setAlignment(Qt.AlignLeft)
            self.connect(editor, SIGNAL("returnPressed()"),
                         self.commitAndCloseEditor)
            return editor
        #---editor = DictEditor for an arbitrary object
        else:
            editor = DictEditor()
            editor.setup(value, key, icon=self.parent().windowIcon(),
                         readonly=readonly)
            self.create_dialog(editor, dict(model=index.model(), editor=editor,
                                            key=key, readonly=readonly))
            return None
        
    def commitAndCloseEditor(self):
        """Overriding method commitAndCloseEditor"""
        editor = self.sender()
        self.emit(SIGNAL("commitData(QWidget*)"), editor)
        self.emit(SIGNAL("closeEditor(QWidget*)"), editor)

    def setEditorData(self, editor, index):
        """Overriding method setEditorData
        Model --> Editor"""
        value = self.get_value(index)
        if isinstance(editor, QLineEdit):
            if not isinstance(value, basestring):
                value = repr(value)
            editor.setText(value)
        elif isinstance(editor, QDateEdit):
            editor.setDate(value)
        elif isinstance(editor, QDateTimeEdit):
            editor.setDateTime(QDateTime(value.date(), value.time()))
            
    def setModelData(self, editor, model, index):
        """Overriding method setModelData
        Editor --> Model"""
        if not hasattr(model, "set_value"):
            # Read-only mode
            return
        if isinstance(editor, QLineEdit):
            value = editor.text()
            try:
                value = display_to_value(to_qvariant(value),
                                         self.get_value(index),
                                         ignore_errors=False)
            except Exception, msg:
                raise
                QMessageBox.critical(editor, _("Edit item"),
                                     _("<b>Unable to assign data to item.</b>"
                                       "<br><br>Error message:<br>%s"
                                       ) % str(msg))
                return
        elif isinstance(editor, QDateEdit):
            qdate = editor.date()
            value = datetime.date( qdate.year(), qdate.month(), qdate.day() )
        elif isinstance(editor, QDateTimeEdit):
            qdatetime = editor.dateTime()
            qdate = qdatetime.date()
            qtime = qdatetime.time()
            value = datetime.datetime( qdate.year(), qdate.month(),
                                       qdate.day(), qtime.hour(),
                                       qtime.minute(), qtime.second() )
        else:
            # Should not happen...
            raise RuntimeError("Unsupported editor widget")
        self.set_value(index, value)
        
class RemoteDictDelegate(DictDelegate):
    """DictEditor Item Delegate"""
    def __init__(self, parent=None, inplace=False,
                 get_value_func=None, set_value_func=None):
        DictDelegate.__init__(self, parent, inplace=inplace)
        self.get_value_func = get_value_func
        self.set_value_func = set_value_func
        
    
    def get_value(self, index):
        if index.isValid():
            item = index.model().getItem(index)
            parent = item.parent()
            parentList = [item]
            while parent != index.model().rootItem:
                parentList.append(parent)
                parent = parent.parent()
            root = parentList.pop()
            name = root.data(0)
            value = self.get_value_func(name)
            itemData = index.model()._get_data(parentList, value)
            return itemData
            
    def set_value(self, index, value):
        if index.isValid():
            item = index.model().getItem(index)
            parent = item.parent()
            item.setData(3, value)
            parentList = [item]
            while parent != index.model().rootItem:
                parentList.append(parent)
                parent = parent.parent()
            
            source = index.model().get_data().get(parentList[-1].data(0)).get('value')
            root = parentList.pop()
            name = root.data(0)
    
            if isinstance(source, (dict,list)):
                newData = self._toData(value, parentList, source)
            elif isinstance(source, (int, float, str)):
                newData = value
            
            self.set_value_func(name, newData)
            
    def _toData(self, value, parentList, data):
        def update(value, parent, data):
            newData = data
            if isinstance(newData, dict):
                updateValue = {parent.data(0): value}
                newData.update(updateValue)
            elif isinstance(newData, (list, tuple)):
                newData[int(parent.data(0)[1:-1])] = value
            elif isinstance(newData, (int, float, str)):
                newData = value
            return newData
        
        def getChildData(child, data):
            if isinstance(data, dict):
                return data.get(child.data(0))
            elif isinstance(data, (list, tuple)):
                ch = child.data(0)[1:-1]
                return data[int(ch)]
            else:
                return data
            
        if len(parentList) == 1:
            p = parentList.pop()
            newData = update(value, p, data)
            return newData
        elif len(parentList) == 0:
            return value
        else :
            p = parentList.pop()
            child = getChildData(p, data)
            childData = self._toData(value, parentList, child)
            newData = update(childData, p, data)
            return newData
    
class RemoteDictEditorTreeView(BaseTreeView):
    """DictEditor table view"""
    def __init__(self, parent, data, truncate=True, minmax=False,
                 inplace=False, collvalue=True, remote_editing=False,
                 get_value_func=None, set_value_func=None,
                 new_value_func=None, remove_values_func=None,
                 copy_value_func=None, is_list_func=None, get_len_func=None,
                 is_array_func=None, is_image_func=None, is_dict_func=None,
                 get_array_shape_func=None, get_array_ndim_func=None,
                 oedit_func=None, plot_func=None, imshow_func=None,
                 show_image_func=None):
        BaseTreeView.__init__(self, parent)
        
        self.remote_editing_enabled = None
        
        self.remove_values = remove_values_func
        self.copy_value = copy_value_func
        self.new_value = new_value_func
        
        self.is_list = is_list_func
        self.get_len = get_len_func
        self.is_array = is_array_func
        self.is_image = is_image_func
        self.is_dict = is_dict_func
        self.get_array_shape = get_array_shape_func
        self.get_array_ndim = get_array_ndim_func
        self.oedit = oedit_func
        self.plot = plot_func
        self.imshow = imshow_func
        self.show_image = show_image_func
        
        self.dictfilter = None
        self.model = None
        self.delegate = None
        self.readonly = False

        
        self.model = DictModel(self, data, names=True,
                               truncate=truncate, minmax=minmax,
                               collvalue=collvalue, remote=True)
                               
        """
        self.model = ReadOnlyTreeModel(self, data, names=True,
                               truncate=truncate, minmax=minmax,
                               collvalue=collvalue, remote=True)
                               """
        self.setModel(self.model)
        
        self.delegate = RemoteDictDelegate(self, inplace,
                                           get_value_func, set_value_func)
        self.setItemDelegate(self.delegate)
        
        
        self.setup_table()
        self.menu = self.setup_menu(truncate, minmax, inplace, collvalue,
                                    remote_editing)

    def setup_menu(self, truncate, minmax, inplace, collvalue, remote_editing):
        """Setup context menu"""
        menu = BaseTreeView.setup_menu(self, truncate, minmax,
                                        inplace, collvalue)
        if menu is None:
            self.remote_editing_action.setChecked(remote_editing)
            return
        
        self.remote_editing_action = create_action(self,
                _( "Edit data in the remote process"),
                tip=_("Editors are opened in the remote process for NumPy "
                      "arrays, PIL images, lists, tuples and dictionaries.\n"
                      "This avoids transfering large amount of data between "
                      "the remote process and Spyder (through the socket)."),
                toggled=self.toggle_remote_editing)
        self.remote_editing_action.setChecked(remote_editing)
        self.toggle_remote_editing(remote_editing)
        add_actions(menu, (self.remote_editing_action,))
        return menu
            
    def toggle_remote_editing(self, state):
        """Toggle remote editing state"""
        self.sig_option_changed.emit('remote_editing', state)
        self.remote_editing_enabled = state

    def oedit_possible(self, key):
        if (self.is_list(key) or self.is_dict(key) 
            or self.is_array(key) or self.is_image(key)):
            # If this is a remote dict editor, the following avoid 
            # transfering large amount of data through the socket
            return True
            
    def edit_item(self):
        """
        Reimplement BaseTreeView's method to edit item
        
        Some supported data types are directly edited in the remote process,
        thus avoiding to transfer large amount of data through the socket from
        the remote process to Spyder
        """
        if self.remote_editing_enabled:
            index = self.currentIndex()
            if not index.isValid():
                return
            key = self.model.getItem(index)
            if self.oedit_possible(key):
                # If this is a remote dict editor, the following avoid
                # transfering large amount of data through the socket
                self.oedit(key)
            else:
                BaseTreeView.edit_item(self)
        else:
            BaseTreeView.edit_item(self)
        
        
        