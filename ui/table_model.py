from PySide6.QtCore import QAbstractTableModel, Qt
import pandas as pd

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0] + 1  # 항상 입력 가능한 빈 행 1개 추가

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                if index.row() < self._data.shape[0]:
                    value = self._data.iloc[index.row(), index.column()]
                    if pd.isna(value): return ""
                    return str(value)
                else:
                    return ""
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self._data.columns):
                    return str(self._data.columns[section])
            if orientation == Qt.Vertical:
                if section < self._data.shape[0]:
                    # 기본 인덱스가 0부터 시작하므로 +1 해서 표시
                    return str(section + 1)
                else:
                    # 새로 추가될 팬텀 행 표시
                    return "*"
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            try:
                row = index.row()
                col = index.column()
                
                # 가상(팬텀) 행을 편집할 때 데이터프레임에 실제 행 추가
                if row == self._data.shape[0]:
                    if not str(value).strip():
                        return False # 빈 값 입력 시 행 추가 안함
                    self.beginInsertRows(index.parent(), row, row)
                    self._data.loc[len(self._data)] = [""] * self._data.shape[1]
                    self.endInsertRows()
                    
                self._data.iloc[row, col] = value
                self.dataChanged.emit(index, index)
                return True
            except:
                return False
        return False
    
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
