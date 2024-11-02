import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QAbstractItemView, QMessageBox, QLabel, QListWidget, QDialog
from PyQt5.QtCore import Qt, QEvent
import schedule_maker
import db
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from datetime import time
db = db.get_db_copy()


class InputDataDialog(QDialog):
    def __init__(self):
        super().__init__()

        with open("InputDataDialog.css", "r") as f:
            self.setStyleSheet(f.read())

        self.vars_to_redact = {
            "Смены групп": "groups_shift",
            "КУГ": "discipline_hours",
            "Преподаватели": "teachers",
            "Аудитории": "rooms",
            "Расписание преподавателей": "teachers_work_hours",
            "Расписание аудиторий": "rooms_availability_hours",
        }

        self.setWindowTitle("Редактирование данных")
        self.setGeometry(100, 100, 1200, 600)

        self.layout = QHBoxLayout(self)

        self.variable_list = QListWidget()
        self.variable_list.setFixedWidth(250)
        self.variable_list.addItems(list(self.vars_to_redact.keys()))
        self.variable_list.currentItemChanged.connect(self.display_variable_data)
        self.layout.addWidget(self.variable_list)

        self.data_table = QTableWidget()
        self.layout.addWidget(self.data_table)

        self.save_button = QPushButton("Сохранить изменения")
        self.save_button.clicked.connect(self.save_changes)
        self.layout.addWidget(self.save_button)

        self.current_variable = None

    def display_variable_data(self, current):
        if not current:
            return

        variable_name = self.vars_to_redact[current.text()]
        self.current_variable = variable_name
        variable_data = getattr(db, variable_name)

        self.data_table.setRowCount(0)

        # Настраиваем отображение таблицы в зависимости от типа переменной
        if variable_name == "groups_shift":
            self.data_table.setColumnCount(3)
            self.data_table.setHorizontalHeaderLabels(["Группа", "Пара", "Время", "Тип"])
            row = 0
            for group, schedule in variable_data.items():
                for pair, time_obj in schedule.items():
                    self.data_table.insertRow(row)
                    self.data_table.setItem(row, 0, QTableWidgetItem(group))
                    self.data_table.setItem(row, 1, QTableWidgetItem(str(pair)))
                    self.data_table.setItem(row, 2, QTableWidgetItem(time_obj.get_str()))
                    self.data_table.setItem(row, 3, QTableWidgetItem(time_obj.pair_type))
                    row += 1

        elif variable_name == "discipline_hours":
            self.data_table.setColumnCount(3)
            self.data_table.setHorizontalHeaderLabels(["Группа", "Дисциплина", "Часы"])
            row = 0
            for group, disciplines in variable_data.items():
                for discipline, hours in disciplines.items():
                    self.data_table.insertRow(row)
                    self.data_table.setItem(row, 0, QTableWidgetItem(group))
                    self.data_table.setItem(row, 1, QTableWidgetItem(discipline))
                    self.data_table.setItem(row, 2, QTableWidgetItem(str(hours)))
                    row += 1

        elif variable_name == "teachers":
            self.data_table.setColumnCount(3)
            self.data_table.setHorizontalHeaderLabels(["Имя", "Дисциплины", "Группы"])
            row = 0
            for name, teacher in variable_data.items():
                self.data_table.insertRow(row)
                self.data_table.setItem(row, 0, QTableWidgetItem(name))
                self.data_table.setItem(row, 1, QTableWidgetItem(", ".join(teacher.disciplines)))
                self.data_table.setItem(row, 2, QTableWidgetItem(", ".join(teacher.groups)))
                row += 1

        elif variable_name == "rooms":
            self.data_table.setColumnCount(2)
            self.data_table.setHorizontalHeaderLabels(["Аудитория", "Онлайн"])
            row = 0
            for room, room_obj in variable_data.items():
                self.data_table.insertRow(row)
                self.data_table.setItem(row, 0, QTableWidgetItem(room))
                self.data_table.setItem(row, 1, QTableWidgetItem("Да" if room_obj.is_online else "Нет"))
                row += 1

        elif variable_name == "teachers_work_hours" or variable_name == "rooms_availability_hours":
            self.data_table.setColumnCount(2)
            self.data_table.setHorizontalHeaderLabels(["Имя", "Расписание"])
            row = 0
            for name, schedule in variable_data.items():
                self.data_table.insertRow(row)
                self.data_table.setItem(row, 0, QTableWidgetItem(name))
                self.data_table.setItem(row, 1, QTableWidgetItem(str(schedule.schedule_for_days)))
                row += 1

        self.data_table.setEditTriggers(QTableWidget.DoubleClicked)

    def save_changes(self):
        if self.current_variable is None:
            return

        variable_data = getattr(db, self.current_variable)

        # Пересоздаем объекты с измененными данными
        if self.current_variable == "groups_shift":
            for row in range(self.data_table.rowCount()):
                group = self.data_table.item(row, 0).text()
                pair = int(self.data_table.item(row, 1).text())
                time_str = self.data_table.item(row, 2).text()
                # Разбор строки времени и пересоздание PairTime объекта
                start_time = time.fromisoformat(time_str.split(" - ")[0])
                end_time = time.fromisoformat(time_str.split(" - ")[1])
                pair_type = self.data_table.item(row, 3).text()
                variable_data[group][pair] = db.PairTime(start_time, end_time, pair_type)

        elif self.current_variable == "discipline_hours":
            for row in range(self.data_table.rowCount()):
                group = self.data_table.item(row, 0).text()
                discipline = self.data_table.item(row, 1).text()
                hours = int(self.data_table.item(row, 2).text())
                variable_data[group][discipline] = hours

        elif self.current_variable == "teachers":
            for row in range(self.data_table.rowCount()):
                name = self.data_table.item(row, 0).text()
                disciplines = set(self.data_table.item(row, 1).text().split(", "))
                groups = set(self.data_table.item(row, 2).text().split(", "))
                variable_data[name] = db.Teacher(name, disciplines, groups)

        elif self.current_variable == "rooms":
            for row in range(self.data_table.rowCount()):
                room = self.data_table.item(row, 0).text()
                is_online = self.data_table.item(row, 1).text() == "Да"
                variable_data[room] = db.Room(is_online)

        elif self.current_variable == "teachers_work_hours" or self.current_variable == "rooms_availability_hours":
            for row in range(self.data_table.rowCount()):
                name = self.data_table.item(row, 0).text()
                schedule_data = eval(self.data_table.item(row, 1).text())
                variable_data[name].schedule_for_days = schedule_data

        setattr(db, self.current_variable, variable_data)


class ErrorDialog(QDialog):
    def __init__(self, errors: list):
        super().__init__()
        self.setWindowTitle("Ошибки при генерации расписания")
        self.setGeometry(100, 100, 600, 500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)  # Добавляем кнопку справки

        # Загрузка стиля
        with open("ErrorDialog.css", "r") as f:
            self.setStyleSheet(f.read())

        self.layout = QVBoxLayout(self)
        self.errors = errors

        # Список ошибок
        self.error_list_widget = QListWidget()
        self.error_list_widget.addItems(
            [f"{i+1} / Группа: {error.group}, Дисциплина: {error.discipline}" for i, error in enumerate(errors)]
        )
        self.error_list_widget.currentItemChanged.connect(self.display_error_info)

        # Заголовок и описание ошибок
        self.help_text = QLabel("Невозможно поставить пары для данных дисциплин и групп:")
        self.layout.addWidget(self.help_text)
        self.layout.addWidget(self.error_list_widget)

        self.group_label = QLabel("| Группа: ")
        self.discipline_label = QLabel("| Дисциплина: ")
        self.hours_label = QLabel("| Оставшиеся часы: ")
        self.layout.addWidget(self.group_label)
        self.layout.addWidget(self.discipline_label)
        self.layout.addWidget(self.hours_label)

    def display_error_info(self, current):
        def pair_text(count):
            if count % 10 == 1: return "пара"
            if count % 10 in [2, 3, 4]: return "пары"
            return "пар"
        if current:
            current_error = self.errors[int(current.text().split("/")[0].strip()) - 1]
            self.group_label.setText(f"| Группа: {current_error.group}")
            self.discipline_label.setText(f"| Дисциплина: {current_error.discipline}")
            self.hours_label.setText(f"| Оставшиеся часы: {current_error.hours} (= {current_error.hours // 2} {pair_text(current_error.hours // 2)})")

    def event(self, event):
        if event.type() == QEvent.Type(124):
            self.show_help()
            return True
        return super().event(event)

    def show_help(self):
        # Отображение справки
        help_message = (
            "В этом окне отображаются ошибки, возникшие при генерации расписания.\n\n"
            "Список вверху содержит информацию о группе и дисциплине, для которой не удалось "
            "поставить пары. Выберите элемент из списка, чтобы увидеть подробные данные "
            "о выбранной ошибке ниже.\n\n"
            "Эта информация поможет вам разобраться с проблемами при создании расписания."
        )
        QMessageBox.information(self, "Справка", help_message)


class MainWindow(QMainWindow):
    def __init__(self):
        self.current_schedule: dict[str, list[db.Pair]] = None
        self.errors = []

        super().__init__()

        self.setWindowTitle("Простое окно с таблицей")
        self.setGeometry(100, 100, 1400, 800)

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
        self.error_button.setEnabled(False)
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

        with open("MainWindow.css", "r") as f:
            self.setStyleSheet(f.read())
        self.resize_columns()

    def resize_columns(self):
        self.table_widget.resizeColumnsToContents()

    def generate_schedule(self):
        pairs, self.errors = schedule_maker.distribute_pairs()
        pairs: dict[str, list[db.Pair]] = schedule_maker.distribute_classrooms(pairs)
        self.current_schedule = pairs
        self.table_widget.setRowCount(0)
        self.table_widget.setHorizontalHeaderLabels(["Группа", "День", "Время", "Предмет", "Педагог", "Каб."])

        rows: list[str] = []
        for group, pairs in pairs.items():
            pairs = sorted(pairs, key=lambda p: db.days.index(p.day))
            for pair in pairs:
                rows.append([group, pair.day, pair.pair_time.get_str(), pair.discipline, pair.teacher, pair.classroom])

        for row in rows:
            current_row = self.table_widget.rowCount()
            self.table_widget.insertRow(current_row)
            for column in range(len(row)):
                self.table_widget.setItem(current_row, column, QTableWidgetItem(row[column]))

        self.resize_columns()
        
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
        input_dialog = InputDataDialog()
        input_dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
