import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from datetime import datetime


class QDialog(QDialog):
    def __init__(self):
        super().__init__()
        global df

class Table(QTableWidget):
    def __init__(self):
        global table_columns, searched_table, df
        super().__init__()
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(table_columns)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(4, 900)

    def print_table_item(self, items: pd.DataFrame):
        self.setRowCount(len(items))
        for i in range(self.rowCount()):
            remove_box = QCheckBox()
            self.setCellWidget(i, 0, remove_box)
            for j in range(1, self.columnCount()):
                self.setItem(i, j, QTableWidgetItem(items.iloc[i, j-1]))


class TableWidget(Table):
    def __init__(self):
        super().__init__()
        if searched_table is not None:
            # 검색 결과인 경우
            searched_table.reset_index(drop=True, inplace=True)
            self.setRowCount(len(searched_table))
            self.print_table_item(searched_table)
        
        else:
            # 전체 조회인 경우
            self.setRowCount(len(df))
            self.print_table_item(df)

        self.cellChanged[int, int].connect(self.infoDF)
        self.cellDoubleClicked[int, int].connect(self.updateDF)

    def updateDF(self, row: int, column: int):
        def _update_item(items: pd.DataFrame):
            info = SearchInfo(items.loc[[row]])
            info.exec_()
            for j in range(1, self.columnCount()):
                self.setItem(row, j, QTableWidgetItem(str(items.iloc[row, j-1])))

        # 더블 클릭 후 정보 수정 시 창을 수정해서 보여줌
        # info 에서 정보가 바뀌면 전체 정보 + 복사된 DataFrame이 모두 바뀌어야 함
        # 전체 DataFrame은 수정되지만 객체에 전달된 복사된 DataFrame은 수정되지 않음
        # 다시 끌어온다.. => 둘 다 global로 사용..
        if searched_table is not None:
        # 검색 결과가 아닌 전체 결과인경우
            _update_item(searched_table)
        else:
        # 전체 결과인 경우
            _update_item(df)

    def infoDF(self, row: int, column: int):
        if searched_table is None:
            # 전체 결과인 경우에만 허락
            text = self.item(row, column).text()
            df.iloc[row, column-1] = text


class TrashBinTableWidget(Table):
    def __init__(self):
        super().__init__()
        global trashbin

        self.setRowCount(len(trashbin))
        self.print_table_item(trashbin)


class TrashBinTable(QDialog):
    def __init__(self):
        super().__init__()
        self.table = TrashBinTableWidget()

        self.setWindowModality(Qt.ApplicationModal)
        self.initUI()
        self.setWindowTitle("휴지통")
        self.resize(1200, 400)
        self.show()

    def initUI(self):
        # Layout 설정
        vbox = QVBoxLayout()
        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()

        # hbox1 widgets 설정
        delete_button = QPushButton("영구삭제", self)
        delete_button.clicked.connect(self.delete_button_clicked)
        vaccum_button = QPushButton("비우기", self)
        vaccum_button.clicked.connect(self.vaccum_button_clicked)

        # hbox1 widgets 추가
        hbox1.addWidget(delete_button)
        hbox1.addWidget(vaccum_button)

        # hbox2 widgets 설정
        restore_button = QPushButton("복구하기", self)
        restore_button.clicked.connect(self.restore_button_clicked)
        cancel_button = QPushButton("닫기", self)
        cancel_button.clicked.connect(self.close)

        # hbox2 widgets 추가
        hbox2.addWidget(restore_button)
        hbox2.addWidget(cancel_button)

        # Layout 설정
        vbox.addWidget(self.table)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

    def delete_button_clicked(self):
        global client_file
        buttonreply = QMessageBox.question(self, '삭제 확인창', '정말로 삭제하시겠습니까?',
                                QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)
        if buttonreply == QMessageBox.Yes:
            global trashbin
            row_line = 0
            remove_list = []

            for i in range(self.table.rowCount()):
                if self.table.cellWidget(row_line, 0).isChecked():
                    remove_list.append(i)
                    self.table.removeRow(row_line)
                else:
                    row_line += 1
            trashbin.drop(remove_list, axis=0, inplace=True)
            trashbin.reset_index(drop=True, inplace=True)
            trashbin.to_pickle(client_file)

    def vaccum_button_clicked(self):
        global trashbin, trashbin_file
        self.table.clear()
        trashbin.drop(trashbin.index, inplace=True)
        trashbin.to_pickle(trashbin_file)
        

    def restore_button_clicked(self):
        global df, trashbin, client_file, trashbin_file
        row_line = 0
        restore_list = []

        for i in range(self.table.rowCount()):
            if self.table.cellWidget(row_line, 0).isChecked():
                restore_list.append(i)
                self.table.removeRow(row_line)
            else:
                row_line += 1

        df = pd.concat([df, trashbin.loc[restore_list]], axis=0, ignore_index=True)
        df.to_pickle(client_file)
        trashbin.drop(restore_list, axis=0, inplace=True)
        trashbin.reset_index(drop=True, inplace=True)
        trashbin.to_pickle(trashbin_file)


class SearchTable(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.table = TableWidget()

        # Layout설정
        mainbox = QVBoxLayout()
        hbox = QHBoxLayout()
        grid = QGridLayout()

        mainbox.addLayout(hbox)
        mainbox.addLayout(grid)
        self.setLayout(mainbox)

        # hbox widget 추가
        hbox.addWidget(self.table)

        # grid widgets 설정
        delete_button = QPushButton("삭제하기", self)
        delete_button.clicked.connect(self.delete_button_clicked)
        delete_button.setShortcut("Ctrl+D")
        delete_button.setShortcut("Ctrl+ㅇ")

        close_button = QPushButton("닫기", self)
        close_button.clicked.connect(self.close)

        # grid widgets 추가
        grid.addWidget(delete_button, 0, 0)
        grid.addWidget(close_button, 0, 1)

        self.setWindowTitle("손놈 조회 결과")
        self.resize(1200, 400)
        self.show()

    def delete_button_clicked(self):
        buttonreply = QMessageBox.question(self, '검색결과 없음', '검색결과가 없습니다. 새로추가하시겠습니까?',
                                QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)
        if buttonreply == QMessageBox.Yes:
            global trashbin, client_file, trashbin_file
            row_line = 0
            remove_list = []

            for i in range(self.table.rowCount()):
                if self.table.cellWidget(row_line, 0).isChecked():
                    remove_list.append(i)
                    self.table.removeRow(row_line)
                else:
                    row_line += 1

            trashbin = pd.concat([trashbin, searched_table.loc[remove_list]], axis=0, ignore_index=True)
            trashbin.to_pickle(trashbin_file)

            # df.drop(df.loc[remove_list].index, axis=0, inplace=True)
            for row in searched_table.loc[remove_list].index:
                name_mask = searched_table.loc[row, '이름']
                birth_mask = searched_table.loc[row, '생년월일']
                num_mask = searched_table.loc[row, '전화번호']
                
                mask = (df['이름'] == name_mask ) & (df['생년월일'] == birth_mask) & (df['전화번호'] == num_mask)
                df.drop(df[mask].index, axis=0, inplace=True)
            df.reset_index(drop=True, inplace=True)
            df.to_pickle(client_file)

            searched_table.drop(remove_list, axis=0, inplace=True)
            searched_table.reset_index(drop=True, inplace=True)
            self.table.print_table_item(searched_table)


class ClientTable(QDialog):
    # 전체 고객 확인 창
    def __init__(self):
        super().__init__()
        self.row = 100_000
        self.col = 5
        self.table = TableWidget()
        self.initUI()

    def initUI(self):
        # Layout 설정
        vbox = QVBoxLayout()
        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()

        # hbox1 widgets 설정
        save_button = QPushButton("저장", self)
        save_button.clicked.connect(self.save_change)
        save_button.setShortcut("Ctrl+S")
        save_button.setShortcut("Ctrl+ㄴ")

        delete_button = QPushButton("삭제", self)
        delete_button.clicked.connect(self.delete_button_clicked)
        delete_button.setShortcut("Ctrl+D")
        delete_button.setShortcut("Ctrl+ㅇ")

        new_client_button = QPushButton("신규추가", self)
        new_client_button.clicked.connect(self.new_client_button_clicked)
        new_client_button.setShortcut("Ctrl+N")
        new_client_button.setShortcut("Ctrl+ㅜ")

        # hbox1 widgets 추가
        hbox1.addWidget(save_button)
        hbox1.addWidget(delete_button)
        hbox1.addWidget(new_client_button)

        # hbox2 widgets 설정
        trashbin_button = QPushButton("휴지통", self)
        trashbin_button.clicked.connect(self.open_trashbin)
        trashbin_button.setShortcut("Ctrl+T")
        trashbin_button.setShortcut("Ctrl+ㅅ")

        cancel_button = QPushButton("닫기", self)
        cancel_button.clicked.connect(self.close)

        # hbox2 widgets 추가
        hbox2.addWidget(trashbin_button)
        hbox2.addWidget(cancel_button)

        # Table 및 Layout 설정
        vbox.addWidget(self.table)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("전체 손놈 확인")
        self.resize(1200, 400)
        self.show()

    def new_client_button_clicked(self):
        new_client = NewClient()
        new_client.exec_()
        self.table.print_table_item(df)

    def open_trashbin(self):
        trashbin_table = TrashBinTable()
        trashbin_table.exec_()
        self.table.print_table_item(df)

    def save_change(self):
        global client_file
        df.to_pickle(client_file)
        self.close()

    def delete_button_clicked(self):
        
        buttonreply = QMessageBox.question(self, '삭제 확인창', '정말로 삭제하시겠습니까?',
                                QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)
        if buttonreply == QMessageBox.Yes:
            global trashbin, client_file, trashbin_file
            row_line = 0
            remove_list = []

            for i in range(self.table.rowCount()):
                if self.table.cellWidget(row_line, 0).isChecked():
                    remove_list.append(i)
                    self.table.removeRow(row_line)
                else:
                    row_line += 1
            trashbin = pd.concat([trashbin, df.loc[remove_list]], axis=0, ignore_index=True)
            trashbin.to_pickle(trashbin_file)
            df.drop(remove_list, axis=0, inplace=True)
            df.reset_index(drop=True, inplace=True)
            df.to_pickle(client_file)
        


class ClientInfo(QDialog):
    '''
    고객 개인 상태창

    이름, 전화번호, 생년월일, 메모
    '''
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        client_layout_save_cancel = QHBoxLayout()
        client_layout_grid_vbox = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(10)

        name_label = QLabel("이름", self)
        phone_number_label = QLabel("전화번호", self)
        birth_label = QLabel("생년월일", self)
        memo_label = QLabel("메모", self)

        self.name_edit = QLineEdit()
        self.phone_number_edit = QLineEdit()
        self.birth_edit = QLineEdit()
        self.memo_edit =  QTextEdit()

        save_button = QPushButton("저장", self)
        save_button.clicked.connect(self.save_button_clicked)
        save_button.setShortcut("Ctrl+S")
        save_button.setShortcut("Ctrl+ㄴ")

        cancel_button = QPushButton("닫기", self)
        cancel_button.clicked.connect(self.close)

        grid.addWidget(name_label, 1, 0)
        grid.addWidget(self.name_edit, 1, 1)
        grid.addWidget(phone_number_label, 2, 0)
        grid.addWidget(self.phone_number_edit, 2, 1)
        grid.addWidget(birth_label, 3, 0)
        grid.addWidget(self.birth_edit, 3, 1)
        grid.addWidget(memo_label, 4, 0)
        grid.addWidget(self.memo_edit, 4, 1, 2, 1)
        
        client_layout_save_cancel.addWidget(save_button)
        client_layout_save_cancel.addWidget(cancel_button)

        client_layout_grid_vbox.addLayout(grid)
        client_layout_grid_vbox.addLayout(client_layout_save_cancel)

        self.setLayout(client_layout_grid_vbox)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(400, 400)
        self.show()

    def save_button_clicked(self):
        pass


class NewClient(ClientInfo):
    '''
    새로운 고객 추가

    이름, 전화번호, 내용
    '''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("새로 오신 손놈 추가")
        
        
    def save_button_clicked(self):
        global df, client_file
        new_row = {'이름': self.name_edit.text(),
                    '전화번호': self.phone_number_edit.text(),
                    '생년월일': self.birth_edit.text(),
                    '내용': self.memo_edit.toPlainText()}
        df = df.append(pd.Series(new_row), ignore_index=True)
        df.to_pickle(client_file)
        self.close()


class AddClient(NewClient):
    def __init__(self, parameter: str=None):
        super().__init__()
        if parameter.isdigit():
            if len(parameter) == 4:
                self.phone_number_edit.setText(parameter)
            elif len(parameter) == 6:
                self.birth_edit.setText(parameter)
        else:
            self.name_edit.setText(parameter)
        

class SearchInfo(ClientInfo):
    def __init__(self, client_data: pd.DataFrame):
        super().__init__()
        global searched_table

        self.client = client_data
        self.name_edit.setText(self.client.iloc[0, 0])
        self.phone_number_edit.setText(self.client.iloc[0, 1])
        self.birth_edit.setText(self.client.iloc[0, 2])
        self.memo_edit.setPlainText(self.client.iloc[0, 3])

    def save_button_clicked(self):
        global client_file
        mask = (df['이름'] == self.client.iloc[0, 0]) & (df['전화번호'] == self.client.iloc[0, 1]) & (df['생년월일'] == self.client.iloc[0, 2])
        if searched_table is not None:
            # 전체 출력이 아닌 검색 출력인 경우
            mask_in_searched = (searched_table['이름'] == self.client.iloc[0, 0]) & (searched_table['전화번호'] == self.client.iloc[0, 1]) & (searched_table['생년월일'] == self.client.iloc[0, 2])
            searched_table.loc[mask_in_searched, '이름'] = self.name_edit.text()
            searched_table.loc[mask_in_searched, '전화번호'] = self.phone_number_edit.text()
            searched_table.loc[mask_in_searched, '생년월일'] = self.birth_edit.text()
            searched_table.loc[mask_in_searched, '내용'] = self.memo_edit.toPlainText()

        df.loc[mask, '이름'] = self.name_edit.text()
        df.loc[mask, '전화번호'] = self.phone_number_edit.text()
        df.loc[mask, '생년월일'] = self.birth_edit.text()
        df.loc[mask, '내용'] = self.memo_edit.toPlainText()
        df.to_pickle(client_file)
        self.close()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # init layout
        self.vbox = QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.grid = QGridLayout()
        # self.hbox_2 = QHBoxLayout()

        # hbox widgets 설정
        self.search_line = QLineEdit()
        self.search_button = QPushButton("조회하기", self)
        self.search_line.returnPressed.connect(self.client_search_button_clicked)
        self.search_button.clicked.connect(self.client_search_button_clicked)

        # hbox widgets 추가
        self.hbox.addWidget(self.search_line)
        self.hbox.addWidget(self.search_button)

        self.vbox.addLayout(self.hbox)

        # grid widgets 설정
        self.whole_search_button = QPushButton("전체조회", self)
        self.whole_search_button.clicked.connect(self.whole_search_button_clicked)
        self.whole_search_button.setShortcut("Ctrl+f")
        self.whole_search_button.setShortcut("Ctrl+ㄹ")
        
        self.new_client_button = QPushButton("신규추가", self)
        self.new_client_button.clicked.connect(self.new_client_button_clicked)
        self.new_client_button.setShortcut("Ctrl+n")
        self.new_client_button.setShortcut("Ctrl+ㅜ")

        self.quit_button = QPushButton("종료", self)
        self.quit_button.clicked.connect(qApp.quit)

        # grid widgets 추가
        self.grid.addWidget(self.whole_search_button, 0, 0)
        self.grid.addWidget(self.new_client_button, 0, 1)
        self.grid.addWidget(self.quit_button, 0, 2)

        self.vbox.addLayout(self.grid)

        # window settings
        self.vbox.setSpacing(0)
        self.hbox.setSpacing(10)
        self.grid.setSpacing(3)
        self.setLayout(self.vbox)
        self.setWindowTitle("덕근씨네 일등약국 고객관리")
        self.setGeometry(800, 300, 100, 50)
        self.show()

    def client_search_result(self, searched_data: pd.DataFrame):
        if len(searched_data) == 1:
            client = SearchInfo(searched_data)
            client.exec_()
        else:
            global searched_table
            searched_table = searched_data
            client = SearchTable()
            client.exec_()
            searched_table = None

    def add_client_button_clicked(self, parameter: str):
        add_client = AddClient(parameter)
        add_client.exec_()

    def new_client_button_clicked(self):
        new_client = NewClient()
        new_client.exec_()        

    def whole_search_button_clicked(self):
        whole_client = ClientTable()
        whole_client.exec_()

    def client_search_button_clicked(self):
        input_str = self.search_line.text()
        # 숫자인 경우 -> 전화번호 or 생년월일
        if input_str.isdigit():
            if len(input_str) == 4:
                # 전화번호를 입력
                searched_data = df.loc[df['전화번호'] == input_str]
            else:
                # 생년월일을 입력
                searched_data = df.loc[df['생년월일'] == input_str]
        else:
            # 이름을 입력
            searched_data = df.loc[df['이름'] == input_str]
        # 1. 결과가 하나인 경우 해당 한 사람 정보만
        # 2. 결과가 둘 이상인 경우 모두 띄우고 누르면 1. 과 같이 창 띄움
        if len(searched_data) == 0:
            # 검색결과가 없는 경우
            buttonreply = QMessageBox.question(self, '검색결과 없음', '검색결과가 없습니다. 새로추가하시겠습니까?',
                                    QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Yes)
            if buttonreply == QMessageBox.Yes:
                self.add_client_button_clicked(input_str)
        else:
            # 검색결과가 있는 경우
            self.client_search_result(searched_data)


table_columns = ['', '이름', '전화번호', '생년월일', '내용']
# python source code 내에서 현재 파일의 위치를 가져옴
os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client_file = f"{BASE_DIR}/drug_store/client_data/client.pkl"
trashbin_file = f"{BASE_DIR}/drug_store/client_data/trashbin.pkl"

df = pd.read_pickle(client_file)
trashbin = pd.read_pickle(trashbin_file)
searched_table = None
app = QApplication(sys.argv)
ex = App()
sys.exit(app.exec_())