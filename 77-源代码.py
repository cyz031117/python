import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QDialog, QFormLayout,
    QDialogButtonBox, QComboBox, QLabel, QSizePolicy, QProgressBar
)
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtGui import QPainter, QColor, QFont
import json
import os
from datetime import datetime

# 预算设置对话框
class BudgetDialog(QDialog):
    def __init__(self, budgets, categories, parent=None):
        super(BudgetDialog, self).__init__(parent)
        self.setWindowTitle("设置预算")
        self.budgets = budgets
        self.categories = categories["支出"]
        
        self.layout = QFormLayout(self)
        
        self.month_combo = QComboBox(self)
        months = [f"{datetime.now().year}-{str(i).zfill(2)}" for i in range(1, 13)]
        self.month_combo.addItems(months)
        self.layout.addRow("月份:", self.month_combo)
        
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(self.categories)
        self.layout.addRow("分类:", self.category_combo)
        
        self.amount_edit = QLineEdit(self)
        self.amount_edit.setPlaceholderText("输入预算金额")
        self.layout.addRow("预算金额:", self.amount_edit)
        
        if budgets:
            current_month = datetime.now().strftime("%Y-%m")
            self.month_combo.setCurrentText(current_month)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
    
    def get_data(self):
        try:
            amount = float(self.amount_edit.text())
        except ValueError:
            amount = 0.0
        return {
            'month': self.month_combo.currentText(),
            'category': self.category_combo.currentText(),
            'amount': amount
        }

# 记账记录对话框
class RecordDialog(QDialog):
    def __init__(self, categories, record=None, parent=None):
        super(RecordDialog, self).__init__(parent)
        self.setWindowTitle("记账记录")
        self.record = record
        self.categories = categories
        
        self.layout = QFormLayout(self)
        
        self.date_edit = QLineEdit(self)
        self.desc_edit = QLineEdit(self)
        self.amount_edit = QLineEdit(self)
        
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(["支出", "收入"])
        self.type_combo.currentIndexChanged.connect(self.update_category_combo)
        
        self.category_combo = QComboBox(self)
        self.update_category_combo()
        
        if record:
            self.date_edit.setText(record['date'])
            self.desc_edit.setText(record['description'])
            self.amount_edit.setText(str(record['amount']))
            index = self.type_combo.findText(record['type'])
            if index != -1:
                self.type_combo.setCurrentIndex(index)
            category_index = self.category_combo.findText(record.get('category', ''))
            if category_index != -1:
                self.category_combo.setCurrentIndex(category_index)
        
        self.layout.addRow("日期:", self.date_edit)
        self.layout.addRow("描述:", self.desc_edit)
        self.layout.addRow("金额:", self.amount_edit)
        self.layout.addRow("类型:", self.type_combo)
        self.layout.addRow("分类:", self.category_combo)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
    
    def update_category_combo(self):
        current_type = self.type_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItems(self.categories.get(current_type, []))
        
    def get_data(self):
        try:
            amount = float(self.amount_edit.text())
        except ValueError:
            amount = 0.0
        return {
            'date': self.date_edit.text(),
            'description': self.desc_edit.text(),
            'amount': amount,
            'type': self.type_combo.currentText(),
            'category': self.category_combo.currentText()
        }

# 分类管理对话框
class CategoryDialog(QDialog):
    def __init__(self, categories, parent=None):
        super(CategoryDialog, self).__init__(parent)
        self.setWindowTitle("分类管理")
        self.categories = categories
        
        self.layout = QVBoxLayout(self)
        
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(["支出", "收入"])
        self.layout.addWidget(self.type_combo)
        
        self.category_list = QTableWidget(0, 2, self)
        self.category_list.setHorizontalHeaderLabels(["分类名称", "操作"])
        self.layout.addWidget(self.category_list)
        
        add_layout = QHBoxLayout()
        self.new_category_edit = QLineEdit(self)
        self.new_category_edit.setPlaceholderText("输入新分类名称")
        add_layout.addWidget(self.new_category_edit)
        
        self.add_button = QPushButton("添加", self)
        self.add_button.clicked.connect(self.add_category)
        add_layout.addWidget(self.add_button)
        self.layout.addLayout(add_layout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        
        self.update_category_list()
        self.type_combo.currentIndexChanged.connect(self.update_category_list)
    
    def update_category_list(self):
        current_type = self.type_combo.currentText()
        categories = self.categories.get(current_type, [])
        self.category_list.setRowCount(0)
        
        for i, category in enumerate(categories):
            row = self.category_list.rowCount()
            self.category_list.insertRow(row)
            
            self.category_list.setItem(row, 0, QTableWidgetItem(category))
            
            delete_btn = QPushButton("删除", self)
            delete_btn.clicked.connect(lambda _, r=row: self.delete_category(r))
            self.category_list.setCellWidget(row, 1, delete_btn)
    
    def add_category(self):
        category = self.new_category_edit.text().strip()
        if not category:
            QMessageBox.warning(self, "警告", "分类名称不能为空")
            return
            
        current_type = self.type_combo.currentText()
        if current_type not in self.categories:
            self.categories[current_type] = []
            
        if category in self.categories[current_type]:
            QMessageBox.warning(self, "警告", "该分类已存在")
            return
            
        self.categories[current_type].append(category)
        self.new_category_edit.clear()
        self.update_category_list()
    
    def delete_category(self, row):
        current_type = self.type_combo.currentText()
        if current_type in self.categories and row < len(self.categories[current_type]):
            del self.categories[current_type][row]
            self.update_category_list()

# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("个人记账管理系统 - 带预算功能")
        self.resize(1200, 750)
        
        self.categories = {
            "支出": ["餐饮", "交通", "购物", "娱乐", "住房"],
            "收入": ["工资", "奖金", "投资", "兼职"]
        }
        self.budgets = []
        self.records = []
        
        self.load_categories()
        self.load_records()
        self.load_budgets()
        
        self.init_ui()
    
    def init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("请输入记录描述关键字...")
        filter_layout.addWidget(self.search_edit)
        
        self.search_button = QPushButton("搜索", self)
        self.search_button.clicked.connect(self.search_records)
        filter_layout.addWidget(self.search_button)
        
        self.filter_combo = QComboBox(self)
        self.filter_combo.addItem("所有分类")
        self.filter_combo.addItems(self.get_all_categories())
        filter_layout.addWidget(self.filter_combo)
        
        self.filter_button = QPushButton("筛选", self)
        self.filter_button.clicked.connect(self.filter_by_category)
        filter_layout.addWidget(self.filter_button)
        
        main_layout.addLayout(filter_layout)
        
        stats_layout = QVBoxLayout()
        
        basic_stats_layout = QHBoxLayout()
        self.total_label = QLabel("总收入: 0.00 | 总支出: 0.00 | 结余: 0.00")
        basic_stats_layout.addWidget(self.total_label)
        
        self.budget_button = QPushButton("预算管理", self)
        self.budget_button.clicked.connect(self.manage_budgets)
        basic_stats_layout.addWidget(self.budget_button)
        
        self.category_button = QPushButton("分类管理", self)
        self.category_button.clicked.connect(self.manage_categories)
        basic_stats_layout.addWidget(self.category_button)
        
        self.chart_button = QPushButton("显示图表", self)
        self.chart_button.clicked.connect(self.show_charts)
        basic_stats_layout.addWidget(self.chart_button)
        
        stats_layout.addLayout(basic_stats_layout)
        
        self.budget_progress_layout = QHBoxLayout()
        self.budget_progress_label = QLabel("本月预算:")
        self.budget_progress_layout.addWidget(self.budget_progress_label)
        
        self.category_progress = {}
        for category in self.categories["支出"]:
            label = QLabel(category)
            progress = QProgressBar()
            progress.setMaximum(100)
            progress.setFormat(f"{category}: %p% (%v/100)")
            progress.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
            self.budget_progress_layout.addWidget(label)
            self.budget_progress_layout.addWidget(progress)
            self.category_progress[category] = progress
        
        stats_layout.addLayout(self.budget_progress_layout)
        main_layout.addLayout(stats_layout)
        
        content_layout = QHBoxLayout()
        
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["日期", "描述", "金额", "类型", "分类"])
        self.table.setSortingEnabled(True)
        content_layout.addWidget(self.table, 3)
        
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumWidth(450)
        self.chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.chart_view, 2)
        
        main_layout.addLayout(content_layout)
        
        btn_layout = QHBoxLayout()
        self.add_button = QPushButton("添加记录", self)
        self.add_button.clicked.connect(self.add_record)
        btn_layout.addWidget(self.add_button)
        self.edit_button = QPushButton("编辑记录", self)
        self.edit_button.clicked.connect(self.edit_record)
        btn_layout.addWidget(self.edit_button)
        self.delete_button = QPushButton("删除记录", self)
        self.delete_button.clicked.connect(self.delete_record)
        btn_layout.addWidget(self.delete_button)
        main_layout.addLayout(btn_layout)
        
        self.refresh_table()
        self.update_stats()
        self.update_charts()
    
    def get_all_categories(self):
        all_categories = []
        for type_categories in self.categories.values():
            all_categories.extend(type_categories)
        return sorted(list(set(all_categories)))
    
    def load_categories(self):
        try:
            if os.path.exists("categories.json"):
                with open("categories.json", "r", encoding="utf-8") as f:
                    self.categories = json.load(f)
        except Exception as e:
            print(f"加载分类数据失败: {e}")
    
    def save_categories(self):
        try:
            with open("categories.json", "w", encoding="utf-8") as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存分类数据失败: {e}")
    
    def load_records(self):
        try:
            if os.path.exists("records.json"):
                with open("records.json", "r", encoding="utf-8") as f:
                    self.records = json.load(f)
        except Exception as e:
            print(f"加载记录失败: {e}")
    
    def save_records(self):
        try:
            with open("records.json", "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记录失败: {e}")
    
    def load_budgets(self):
        try:
            if os.path.exists("budgets.json"):
                with open("budgets.json", "r", encoding="utf-8") as f:
                    self.budgets = json.load(f)
        except Exception as e:
            print(f"加载预算数据失败: {e}")
    
    def save_budgets(self):
        try:
            with open("budgets.json", "w", encoding="utf-8") as f:
                json.dump(self.budgets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存预算数据失败: {e}")
    
    def refresh_table(self, records=None):
        if records is None:
            records = self.records
        self.table.setRowCount(0)
        for rec in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(rec['date']))
            self.table.setItem(row, 1, QTableWidgetItem(rec['description']))
            
            amount_item = QTableWidgetItem(f"{rec['amount']:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, amount_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(rec['type']))
            self.table.setItem(row, 4, QTableWidgetItem(rec.get('category', '')))
        
        self.table.resizeColumnsToContents()
        self.save_records()
        self.update_stats()
        self.update_charts()
    
    def update_stats(self):
        total_income = sum(rec['amount'] for rec in self.records if rec['type'] == "收入")
        total_expense = sum(rec['amount'] for rec in self.records if rec['type'] == "支出")
        balance = total_income - total_expense
        
        self.total_label.setText(
            f"总收入: {total_income:.2f} | 总支出: {total_expense:.2f} | 结余: {balance:.2f}"
        )
        
        self.update_budget_progress()
    
    def update_budget_progress(self):
        current_month = datetime.now().strftime("%Y-%m")
        monthly_expenses = self.get_monthly_expenses(current_month)
        
        for category in self.categories["支出"]:
            progress = self.category_progress[category]
            budget = next((b for b in self.budgets if 
                         b['month'] == current_month and 
                         b['category'] == category), None)
            
            if budget:
                budget_amount = budget['amount']
                expense = monthly_expenses.get(category, 0)
                percentage = min(100, (expense / budget_amount) * 100) if budget_amount > 0 else 0
                
                progress.setValue(int(percentage))
                progress.setFormat(f"{category}: %p% (¥{expense:.2f}/¥{budget_amount:.2f})")
                
                if percentage >= 100:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
                    QMessageBox.warning(self, "预算超支", f"{category}分类已超支！")
                elif percentage >= 80:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
                else:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
            else:
                progress.setValue(0)
                progress.setFormat(f"{category}: 未设置预算")
    
    def get_monthly_expenses(self, month):
        expenses = {}
        for rec in self.records:
            if rec['type'] == "支出":
                try:
                    record_month = datetime.strptime(rec['date'], "%Y-%m-%d").strftime("%Y-%m")
                    if record_month == month:
                        category = rec.get('category', '其他')
                        expenses[category] = expenses.get(category, 0) + rec['amount']
                except ValueError:
                    continue
        return expenses
    
    def update_charts(self):
        expense_series = QPieSeries()
        expense_series.setName("支出分类")
        
        current_month = datetime.now().strftime("%Y-%m")
        expense_data = self.get_monthly_expenses(current_month)
        
        colors = [QColor(255, 99, 132), QColor(54, 162, 235), QColor(255, 206, 86),
                 QColor(75, 192, 192), QColor(153, 102, 255), QColor(255, 159, 64)]
        
        for i, (category, amount) in enumerate(expense_data.items()):
            budget = next((b for b in self.budgets if 
                         b['month'] == current_month and 
                         b['category'] == category), None)
            
            label = f"{category}: ¥{amount:.2f}"
            if budget:
                label += f" (预算:¥{budget['amount']:.2f})"
                if amount > budget['amount']:
                    label += "⚠️"
            
            slice = expense_series.append(label, amount)
            slice.setColor(colors[i % len(colors)])
            slice.setLabelVisible(True)
            slice.setLabelPosition(QPieSlice.LabelOutside)
            slice.setLabelFont(QFont("Arial", 8))
        
        chart = QChart()
        chart.addSeries(expense_series)
        chart.setTitle(f"{current_month}支出分类占比 (带预算对比)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chart.setMargins(QMargins(5, 5, 5, 5))
        
        self.chart_view.setChart(chart)
    
    def show_charts(self):
        if self.chart_view.isVisible():
            self.chart_view.hide()
            self.chart_button.setText("显示图表")
        else:
            self.chart_view.show()
            self.chart_button.setText("隐藏图表")
            self.update_charts()
    
    def add_record(self):
        dialog = RecordDialog(self.categories, parent=self)
        if dialog.exec_():
            new_record = dialog.get_data()
            self.records.append(new_record)
            self.refresh_table()
    
    def edit_record(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要编辑的记录")
            return
        row = selected_items[0].row()
        record = self.records[row]
        dialog = RecordDialog(self.categories, record, parent=self)
        if dialog.exec_():
            self.records[row] = dialog.get_data()
            self.refresh_table()
    
    def delete_record(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要删除的记录")
            return
        row = selected_items[0].row()
        del self.records[row]
        self.refresh_table()
    
    def search_records(self):
        keyword = self.search_edit.text().lower()
        if not keyword:
            self.refresh_table()
            return
        filtered = [rec for rec in self.records if keyword in rec['description'].lower()]
        self.refresh_table(filtered)
    
    def filter_by_category(self):
        selected_category = self.filter_combo.currentText()
        if selected_category == "所有分类":
            self.refresh_table()
            return
        
        filtered = [rec for rec in self.records if rec.get('category', '') == selected_category]
        self.refresh_table(filtered)
    
    def manage_categories(self):
        dialog = CategoryDialog(self.categories, parent=self)
        if dialog.exec_():
            self.filter_combo.clear()
            self.filter_combo.addItem("所有分类")
            self.filter_combo.addItems(self.get_all_categories())
            self.save_categories()
    
    def manage_budgets(self):
        dialog = BudgetDialog(self.budgets, self.categories, parent=self)
        if dialog.exec_():
            new_budget = dialog.get_data()
            existing = next((b for b in self.budgets if 
                           b['month'] == new_budget['month'] and 
                           b['category'] == new_budget['category']), None)
            if existing:
                existing['amount'] = new_budget['amount']
            else:
                self.budgets.append(new_budget)
            self.save_budgets()
            self.update_budget_progress()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())