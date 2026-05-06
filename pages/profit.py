from typing import Any


def build_profit_tab(gui: Any) -> None:
    frame = gui.ttk.Frame(gui.notebook)
    gui.notebook.add(frame, text="利润统计")
    gui.ttk.Button(frame, text="刷新统计", command=gui.refresh_profit).pack(anchor="w", padx=6, pady=6)
    gui.profit_text = gui.tk.Text(frame, height=36, wrap="word")
    gui.profit_text.pack(fill="both", expand=True, padx=4, pady=8)
