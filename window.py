import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Простое окно с таблицей")
        self.setGeometry(100, 100, 600, 400)

        # Создаем виджет для центральной области
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Создаем вертикальный макет
        self.layout = QVBoxLayout(self.central_widget)

        # Создаем таблицу
        self.table_widget = QTableWidget(5, 3)  # 5 строк и 3 столбца
        self.table_widget.setHorizontalHeaderLabels(["Имя", "Возраст", "Город"])  # Заголовки столбцов

        # Заполнение таблицы примерными данными
        self.populate_table()

        # Кнопка для добавления новой строки
        self.add_button = QPushButton("Добавить строку")
        self.add_button.clicked.connect(self.add_row)

        # Добавляем виджеты в макет
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.add_button)

        # Применяем стили
        self.setStyleSheet(self.load_styles())
        self.resize_columns()

    def resize_columns(self):
        self.table_widget.resizeColumnsToContents()

    def populate_table(self):
        data = [
            ["Алексей", "30", "Москва"],
            ["Мария", "25", "Санкт-Петербург"],
            ["Иван", "35", "Казань"],
            ["Ольга", "28", "Екатеринбург"],
            ["Дмитрий", "40", "Новосибирск"]
        ]
        
        for row in range(len(data)):
            for column in range(len(data[row])):
                self.table_widget.setItem(row, column, QTableWidgetItem(data[row][column]))

    def add_row(self):
        current_row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(current_row_count)  # Добавляем новую строку

    def load_styles(self):
        return """
            QWidget {
                font: 11pt "MS Shell Dlg 2";
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QTableWidget {
                font-family: Arial, sans-serif;
                font-size:20px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #d1e7dd; /* Цвет выделенной строки */
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049; /* Цвет кнопки при наведении */
            }
        """

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())