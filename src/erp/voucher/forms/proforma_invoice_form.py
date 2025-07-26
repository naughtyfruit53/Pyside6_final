# src/erp/voucher/forms/proforma_invoice_form.py

from src.erp.logic.utils.forms_utils import *
from src.erp.logic.utils.sequence_utils import get_next_proforma_sequence, increment_proforma_sequence

class ProformaInvoiceForm(QWidget):
    def __init__(self, parent=None, app=None, module_name=None, voucher_type_id=None, voucher_type_name=None, voucher_data=None, voucher_management=None, voucher_category=None, voucher_name=None, save_callback=None, add_product_callback=None, entities=None, products=None, payment_terms=None):
        super().__init__(parent)
        self.app = app
        self.module_name = module_name
        self.voucher_type_id = voucher_type_id
        self.voucher_type_name = voucher_type_name if voucher_type_name else "Proforma Invoice"
        self.voucher_management = voucher_management
        common_init(self, self.voucher_type_name, voucher_data, get_products, get_payment_terms)
        self.entities = get_customers()
        self.setObjectName("ProformaInvoiceForm")
        apply_stylesheet(self, "proforma_invoice_form.qss")
        self.setup_ui()

    def setup_ui(self):
        logger.info(f"Creating Proforma Invoice form (ID: {self.voucher_type_id})")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(5)  # Reduce spacing between elements

        # Title
        title_label = create_title_label("Create Proforma Invoice")
        self.content_layout.addWidget(title_label)

        # Header row: Voucher Number, Date, Validity Date
        header_fields = [
            ("Voucher Number*", 'text', "Voucher Number", get_next_proforma_sequence() or ''),
            ("Date*", 'date', "Voucher Date", self.voucher_data.get("Voucher Date", QDate.currentDate().toString("yyyy-MM-dd"))),
            ("Validity Date", 'date', "Validity Date", self.voucher_data.get("Validity Date", QDate.currentDate().toString("yyyy-MM-dd")))
        ]
        header_row, header_entries = create_header_row(header_fields)
        self.content_layout.addLayout(header_row)
        self.entries.update(header_entries)

        # Party row
        party_row, self.party_combo, self.payment_combo = create_party_row("Customer", self.entities, self.payment_terms, self.voucher_data)
        self.content_layout.addLayout(party_row)
        self.entries["Party Name"] = self.party_combo
        self.entries["Payment Terms"] = self.payment_combo

        # Set handlers for party combo
        self.party_combo.lineEdit().textChanged.connect(lambda text: handle_text_changed(text, self.party_combo, self.entities))
        self.party_combo.activated.connect(lambda index: self.handle_party_activated(index, self.party_combo, "Customer"))
        self.party_combo.lineEdit().returnPressed.connect(lambda: self.handle_party_return_pressed(self.party_combo, "Customer"))

        # Product table
        self.item_table = create_product_table()
        self.content_layout.addWidget(self.item_table)

        # Remove button
        remove_button = create_remove_button(lambda: remove_product(self.item_table, self.product_rows, lambda rows: update_totals(rows, self.total_amount, self.amount_in_words)))
        self.content_layout.addWidget(remove_button)

        # Total and words
        total_layout, words_layout, self.total_amount, self.amount_in_words = create_total_words()
        self.content_layout.addLayout(total_layout)
        self.content_layout.addLayout(words_layout)

        # Bottom layout
        bottom_layout = create_bottom_layout(self.app, self.voucher_type_name, self.save_voucher, lambda: self.app.show_frame("home"))
        self.content_layout.addLayout(bottom_layout)

        main_layout.addWidget(scroll)
        populate_product_table(self.item_table, self.product_rows, add_new_row, self.products, self.handle_activated, self.handle_return_pressed)
        self.update_product_frame_position()

    def handle_party_activated(self, index, combo, party_type):
        text = combo.itemText(index)
        if text.startswith("Add "):
            if text == f"Add New {party_type}":
                combo.lineEdit().setText("")
            else:
                suggested = text.split('"')[1]
                combo.lineEdit().setText(suggested)
            if party_type == "Customer":
                add_customer_callback(self, combo, self.voucher_management)
            else:
                add_vendor_callback(self, combo, self.voucher_management)
            self.refresh_party_combo(combo, party_type)

    def handle_party_return_pressed(self, combo, party_type):
        text = combo.lineEdit().text().strip()
        if not text:
            return
        index = combo.findText(text, Qt.MatchExactly)
        if index != -1:
            self.handle_party_activated(index, combo, party_type)
        else:
            add_idx = find_add_item(combo)
            if add_idx == -1:
                new_text = f'Add "{text}" as new {party_type.lower()}'
                combo.insertItem(0, new_text)
                add_idx = 0
            self.handle_party_activated(add_idx, combo, party_type)

    def refresh_party_combo(self, combo, party_type):
        combo.clear()
        self.entities = get_customers()
        party_names = self.entities
        combo.addItems(party_names)
        if not party_names:
            combo.addItem(f"Add New {party_type}")
            combo.setCurrentIndex(0)
        else:
            combo.insertItem(0, f"Add New {party_type}")
            combo.setCurrentIndex(-1)
        completer = QCompleter(combo.model())
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        combo.setCompleter(completer)

    def handle_activated(self, index, combo, row):
        text = combo.itemText(index)
        if text.startswith("Add "):
            if text == "Add New Product":
                combo.lineEdit().setText("")
            else:
                suggested = text.split('"')[1]
                combo.lineEdit().setText(suggested)
            callback_to_use = self.add_product_cb if self.add_product_cb else add_product_callback
            callback_to_use(self, combo, self.voucher_management, self.voucher_type_id, self.products, self.app.font(), [100] * 7, self.update_product_frame_position, lambda table: populate_product_table(table, self.product_rows, add_new_row, self.products, self.handle_activated, self.handle_return_pressed))
        elif text:
            open_add_quantity_dialog(text, row, combo, self.products, lambda dialog, pid, n, h, u, gt, qt, pt, r, c, s: save_quantity_dialog(dialog, pid, n, h, u, gt, qt, pt, r, c, s, self.products, self.item_table, self.product_rows, lambda rows: update_totals(rows, self.total_amount, self.amount_in_words), self.app, "Sales" in self.voucher_type_name, self))

    def handle_return_pressed(self, combo, row):
        text = combo.lineEdit().text().strip()
        if not text:
            return
        index = combo.findText(text, Qt.MatchExactly)
        if index != -1:
            self.handle_activated(index, combo, row)
        else:
            add_idx = find_add_item(combo)
            if add_idx == -1:
                new_text = f'Add "{text}" as new product'
                combo.insertItem(0, new_text)
                add_idx = 0
            self.handle_activated(add_idx, combo, row)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_product_frame_position()

    def update_product_frame_position(self):
        pass

    def save_voucher(self):
        save_voucher(self, ["Voucher Number", "Voucher Date", "Party Name"], increment_proforma_sequence)