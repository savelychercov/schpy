import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QAbstractItemView, QMessageBox, QLabel, QListWidget, QDialog
import schedule_maker
import db
from openpyxl import Workbook
from openpyxl.utils import get_column_letter


class ErrorDialog(QDialog):
    def __init__(self, errors):
        super().__init__()
        self.setWindowTitle("Ошибки при генерации расписания")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet(self.load_styles())

        self.layout = QVBoxLayout(self)
        self.errors = errors

        self.error_list_widget = QListWidget()
        self.error_list_widget.addItems([f"{i+1} / Группа: {error.group}, Дисциплина: {error.discipline}" for i, error in enumerate(errors)])
        self.error_list_widget.currentItemChanged.connect(self.display_error_info)

        self.layout.addWidget(self.error_list_widget)

        self.group_label = QLabel("Группа: ")
        self.discipline_label = QLabel("Дисциплина: ")
        self.layout.addWidget(self.group_label)
        self.layout.addWidget(self.discipline_label)

    def display_error_info(self, current):
        if current:
            current_error = self.errors[int(current.text().split("/")[0].strip()) - 1]
            self.group_label.setText(f"Группа: {current_error.group}")
            self.discipline_label.setText(f"Дисциплина: {current_error.discipline}")

    def load_styles(self):
        with open("ErrorDialog.css", "r") as f:
            return f.read()


class MainWindow(QMainWindow):
    def __init__(self):
        self.current_schedule: dict[str, list[db.Pair]] = None
        self.errors = []  # Список для хранения ошибок

        super().__init__()

        self.setWindowTitle("Простое окно с таблицей")
        self.setGeometry(100, 100, 1200, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        self.table_widget = QTableWidget(1, 6)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.button_layout = QVBoxLayout()

        self.generate_schedule_button = QPushButton("Сгенерировать расписание")
        self.generate_schedule_button.clicked.connect(self.generate_schedule)
        self.button_layout.addWidget(self.generate_schedule_button)

        self.error_button = QPushButton(f"Ошибки: {len(self.errors)}")
        self.error_button.setEnabled(False)  # Изначально отключено
        self.error_button.clicked.connect(self.show_errors)
        self.button_layout.addWidget(self.error_button)

        self.export_schedule_button = QPushButton("Выгрузить расписание")
        self.export_schedule_button.clicked.connect(self.export_schedule)
        self.button_layout.addWidget(self.export_schedule_button)

        self.input_data_button = QPushButton("Ввод данных")
        self.input_data_button.clicked.connect(self.input_data)
        self.button_layout.addWidget(self.input_data_button)

        self.layout.addWidget(self.table_widget)
        self.layout.addLayout(self.button_layout)

        self.button_layout.addStretch()

        self.setStyleSheet(self.load_styles())
        self.resize_columns()

    def resize_columns(self):
        self.table_widget.resizeColumnsToContents()

    def generate_schedule(self):
        pairs, self.errors = schedule_maker.make_full_schedule()
        pairs: dict[str, list[db.Pair]] = schedule_maker.distribute_classrooms(pairs)
        self.current_schedule = pairs
        self.table_widget.setRowCount(0)
        self.table_widget.setHorizontalHeaderLabels(["Группа", "День", "Время", "Предмет", "Педагог", "Каб."])

        rows: list[str] = []
        for group, pairs in pairs.items():
            pairs = sorted(pairs, key=lambda pair: db.days.index(pair.day))
            for pair in pairs:
                rows.append([group, pair.day, pair.pair_time.get_str(), pair.discipline, pair.teacher, pair.classroom])

        for row in rows:
            current_row = self.table_widget.rowCount()
            self.table_widget.insertRow(current_row)
            for column in range(len(row)):
                self.table_widget.setItem(current_row, column, QTableWidgetItem(row[column]))

        self.resize_columns()
        
        # Обновляем кнопку ошибок
        self.error_button.setText(f"Ошибки: {len(self.errors)}")
        self.error_button.setEnabled(len(self.errors) > 0)

    def show_errors(self):
        if self.errors:
            error_dialog = ErrorDialog(self.errors)
            error_dialog.exec_()

    def export_schedule(self):
        try:
            row_count = self.table_widget.rowCount()
            column_count = self.table_widget.columnCount()

            data = []
            for row in range(row_count):
                row_data = []
                for column in range(column_count):
                    item = self.table_widget.item(row, column)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            headers = [self.table_widget.horizontalHeaderItem(i).text() for i in range(column_count)]

            workbook = Workbook()
            sheet = workbook.active

            for col_num, header in enumerate(headers, 1):
                sheet.cell(row=1, column=col_num, value=header)

            for row_num, row_data in enumerate(data, 2):
                for col_num, value in enumerate(row_data, 1):
                    sheet.cell(row=row_num, column=col_num, value=value)

            for col in range(1, column_count + 1):
                max_length = 0
                column_letter = get_column_letter(col)
                for row in range(1, row_count + 2):
                    cell_value = sheet[f"{column_letter}{row}"].value
                    if cell_value:
                        max_length = max(max_length, len(str(cell_value)))
                adjusted_width = (max_length + 2)
                sheet.column_dimensions[column_letter].width = adjusted_width

            workbook.save("расписание.xlsx")
            resp = QMessageBox.information(
                self,
                "Успех",
                "Расписание успешно выгружено\nОткрыть xlsx файл?",
                buttons=QMessageBox.Ok | QMessageBox.Cancel
            )

            if resp == QMessageBox.Ok:
                import os
                os.startfile("расписание.xlsx")
        except AttributeError:
            QMessageBox.warning(self, "Ошибка", "Сгенерируйте расписание перед выгрузкой")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            raise e

    def input_data(self):
        pass

    def load_styles(self):
        with open("MainWindow.css", "r") as f:
            return f.read()

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
