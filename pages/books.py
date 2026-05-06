from typing import Any


def build_books_tab(gui: Any) -> None:
    frame = gui.ttk.Frame(gui.notebook)
    gui.notebook.add(frame, text="图书资料库")

    top = gui.ttk.Frame(frame)
    top.pack(fill="x", pady=6)
    gui.book_search_var = gui.tk.StringVar()
    gui.ttk.Label(top, text="搜索：").pack(side="left")
    gui.ttk.Entry(top, textvariable=gui.book_search_var, width=30).pack(side="left", padx=5)
    gui.ttk.Button(top, text="查询", command=gui.refresh_books).pack(side="left", padx=4)
    gui.ttk.Button(top, text="刷新", command=gui.refresh_books).pack(side="left", padx=4)

    table_frame = gui.ttk.Frame(frame)
    table_frame.pack(fill="both", expand=True)
    columns = ("sku", "name", "price", "discount", "shipping_fee", "publisher")
    gui.book_tree = gui.ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
    headers = {
        "sku": "SKU/书号",
        "name": "书名",
        "price": "定价",
        "discount": "折扣",
        "shipping_fee": "邮费",
        "publisher": "出版社",
    }
    widths = {"sku": 120, "name": 360, "price": 80, "discount": 80, "shipping_fee": 80, "publisher": 180}
    for col in columns:
        gui.book_tree.heading(col, text=headers[col])
        gui.book_tree.column(col, width=widths[col], anchor="center")
    ybar = gui.ttk.Scrollbar(table_frame, orient="vertical", command=gui.book_tree.yview)
    gui.book_tree.configure(yscrollcommand=ybar.set)
    gui.book_tree.pack(side="left", fill="both", expand=True)
    ybar.pack(side="right", fill="y")

    form = gui.ttk.LabelFrame(frame, text="新增 / 编辑图书")
    form.pack(fill="x", pady=10)
    gui.book_vars = {
        "sku": gui.tk.StringVar(),
        "name": gui.tk.StringVar(),
        "price": gui.tk.StringVar(),
        "discount": gui.tk.StringVar(value="0.65"),
        "shipping_fee": gui.tk.StringVar(value="6"),
        "publisher": gui.tk.StringVar(),
        "supplier": gui.tk.StringVar(),
    }
    book_fields = [
        ("SKU/书号", "sku"),
        ("书名", "name"),
        ("定价", "price"),
        ("折扣", "discount"),
        ("邮费", "shipping_fee"),
        ("出版社", "publisher"),
        ("供应商", "supplier"),
    ]
    for idx, (label, key) in enumerate(book_fields):
        row = idx // 3
        col = (idx % 3) * 2
        gui.ttk.Label(form, text=label).grid(row=row, column=col, sticky="e", padx=6, pady=4)
        gui.ttk.Entry(form, textvariable=gui.book_vars[key], width=30).grid(row=row, column=col + 1, sticky="w", padx=6, pady=4)
    gui.ttk.Button(form, text="保存图书资料", command=gui.save_book).grid(row=3, column=0, columnspan=2, padx=8, pady=8, sticky="w")
