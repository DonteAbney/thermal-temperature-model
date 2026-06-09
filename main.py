import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import numpy as np
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from frontside_temp import tempatureFront

WIN_BG = "#c0c0c0"
WIN_DARK = "#808080"
WIN_LITE = "#ffffff"
WIN_NAVY = "#000080"
TXT = "#000000"
ENTRY_BG = "#ffffff"
BTN_BG = "#c0c0c0"

FONT_LABEL = ("Times News Roman", 10)
FONT_BOLD = ("Times News Roman", 10, "bold")
FONT_TITLE = ("Times News Roman", 12, "bold")
FONT_MONO = ("Times News Roman", 10)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def custom_frame(parent, relief="raised", **kw):
    return ctk.CTkFrame(
        parent,
        corner_radius=0,
        fg_color=WIN_BG,
        border_width=2,
        border_color=WIN_DARK,
        **kw,
    )


def custom_label(parent, text, **kw):
    return ctk.CTkLabel(
        parent, text=text, font=FONT_LABEL, text_color=TXT, fg_color="transparent", **kw
    )


def custom_entry(parent, **kw):
    return ctk.CTkEntry(
        parent,
        corner_radius=0,
        fg_color=ENTRY_BG,
        text_color=TXT,
        border_color=WIN_DARK,
        border_width=2,
        font=FONT_MONO,
        **kw,
    )


def custom_button(parent, text, command, **kw):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        corner_radius=0,
        fg_color=BTN_BG,
        text_color=TXT,
        hover_color="#a0a0a0",
        border_width=2,
        border_color=WIN_DARK,
        font=FONT_BOLD,
        **kw,
    )


def custom_check(parent, text, variable, command=None, **kw):
    return ctk.CTkCheckBox(
        parent,
        text=text,
        variable=variable,
        command=command,
        corner_radius=0,
        fg_color=WIN_NAVY,
        hover_color=WIN_DARK,
        border_color=WIN_DARK,
        border_width=2,
        text_color=TXT,
        font=FONT_LABEL,
        checkmark_color=WIN_LITE,
        **kw,
    )


def make_title_bar(parent, title):
    bar = ctk.CTkFrame(parent, corner_radius=0, fg_color=WIN_NAVY, height=24)
    bar.pack(fill="x", side="top")
    ctk.CTkLabel(
        bar,
        text=title,
        font=FONT_BOLD,
        text_color="white",
        fg_color="transparent",
    ).pack(side="left", padx=6, pady=2)
    return bar


class ThermalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Frontside Temperature Finder")
        self.configure(fg_color=WIN_BG)
        self.geometry("1100x720")
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_plot_panel()
        self._toggle_fourth()

        self.bind("<Escape>", lambda e: self.destroy())

    def _build_sidebar(self):
        outer = custom_frame(self)
        outer.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        outer.grid_propagate(False)
        outer.configure(width=310)

        make_title_bar(outer, "  Parameters")

        scroll = ctk.CTkScrollableFrame(
            outer,
            corner_radius=0,
            fg_color=WIN_BG,
            scrollbar_button_color=WIN_DARK,
            scrollbar_button_hover_color="#606060",
        )
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        scroll.grid_columnconfigure(0, weight=1)

        self.fourth_var = ctk.BooleanVar(value=True)
        chk = custom_check(
            scroll, "T^4 Dependence", self.fourth_var, command=self._toggle_fourth
        )
        chk.grid(row=0, column=0, padx=8, pady=(10, 6), sticky="w")

        sep = ctk.CTkFrame(scroll, height=2, fg_color=WIN_DARK, corner_radius=0)
        sep.grid(row=1, column=0, sticky="ew", padx=8, pady=4)

        self._fields_meta = [
            ("τ  (thickness) [m]", "tau", "1.0", False),
            ("T_wall  [K]", "t_wall", "300.0", True),
            ("k  (thermal conductivity)", "k", "1.0", False),
            ("ε_f  (epsilon front)", "epsilon_f", "0.9", True),
            ("ε_b  (epsilon back)", "epsilon_b", "0.8", False),
            ("A  (area)  [m²]", "a_area", "1.0", False),
            ("Z  (factor)", "z", "1.0", False),
            ("P_max  [W]", "p_max", "100.0", False),
            ("T_b  (back temp) [K]", "t_b", "300.0", False),
        ]

        self._entry_widgets = {}
        self._row_widgets = {}

        for i, (lbl_txt, attr, default, fourth_only) in enumerate(self._fields_meta):
            row_base = 2 + i * 2
            lbl = custom_label(scroll, lbl_txt)
            lbl.grid(row=row_base, column=0, padx=10, pady=(6, 0), sticky="w")
            ent = custom_entry(scroll, width=220)
            ent.insert(0, default)
            ent.grid(row=row_base + 1, column=0, padx=10, pady=(0, 2), sticky="ew")
            self._entry_widgets[attr] = ent
            self._row_widgets[attr] = (lbl, ent)

        sep2 = ctk.CTkFrame(scroll, height=2, fg_color=WIN_DARK, corner_radius=0)
        sep2.grid(
            row=2 + len(self._fields_meta) * 2, column=0, sticky="ew", padx=8, pady=6
        )

        self.btn_submit = custom_button(scroll, "  CALCULATE  ", self._on_submit)
        self.btn_submit.grid(
            row=3 + len(self._fields_meta) * 2, column=0, padx=10, pady=8, sticky="ew"
        )

        res_outer = ctk.CTkFrame(
            scroll, corner_radius=0, fg_color=WIN_DARK, border_width=0
        )
        res_outer.grid(
            row=4 + len(self._fields_meta) * 2,
            column=0,
            padx=10,
            pady=(4, 10),
            sticky="ew",
        )
        res_inner = ctk.CTkFrame(res_outer, corner_radius=0, fg_color=ENTRY_BG)
        res_inner.pack(padx=2, pady=2, fill="both")

        self.result_label = ctk.CTkLabel(
            res_inner,
            text="",
            font=FONT_LABEL,
            text_color=TXT,
            fg_color=ENTRY_BG,
            justify="left",
            wraplength=230,
            anchor="nw",
        )
        self.result_label.pack(padx=6, pady=6, fill="both")

    def _build_plot_panel(self):
        outer = custom_frame(self)
        outer.grid(row=0, column=1, sticky="nsew", padx=(0, 6), pady=6)

        make_title_bar(outer, "  Tf vs Tb")

        plot_container = ctk.CTkFrame(outer, corner_radius=0, fg_color=WIN_BG)
        plot_container.pack(fill="both", expand=True, padx=4, pady=4)

        self.fig = Figure(facecolor=WIN_BG, edgecolor=WIN_DARK)
        self.ax = self.fig.add_subplot(111)
        self._style_axes(self.ax)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_container)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, plot_container)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        self._draw_placeholder()

    def _style_axes(self, ax):
        ax.set_facecolor(WIN_LITE)
        self.fig.patch.set_facecolor(WIN_BG)
        ax.tick_params(colors=TXT, labelsize=8)
        ax.xaxis.label.set_color(TXT)
        ax.yaxis.label.set_color(TXT)
        ax.title.set_color(TXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(WIN_DARK)
        ax.grid(True, color="#dddddd", linestyle="--", linewidth=0.5)

    def _draw_placeholder(self):
        self.ax.clear()
        self._style_axes(self.ax)
        self.canvas.draw()

    def _toggle_fourth(self):
        fourth_on = self.fourth_var.get()
        for _, attr, _, fourth_only in self._fields_meta:
            if fourth_only:
                lbl, ent = self._row_widgets[attr]
                if fourth_on:
                    lbl.grid()
                    ent.grid()
                    ent.configure(state="normal", fg_color=ENTRY_BG)
                else:
                    lbl.grid_remove()
                    ent.grid_remove()

        self.ax.clear()
        self._style_axes(self.ax)
        self.canvas.draw()
        self.result_label.configure(text="")

    def _on_submit(self):
        try:
            vals = {}
            for _, attr, _, _ in self._fields_meta:
                if self._entry_widgets[attr].winfo_ismapped():
                    val_str = self._entry_widgets[attr].get().strip()
                    if not val_str:
                        raise ValueError("All visible inputs must be filled.")
                    vals[attr] = float(val_str)

            fourth = self.fourth_var.get()

            tau = vals.get("tau", 1.0)
            t_wall = vals.get("t_wall", 300.0)
            k = vals.get("k", 1.0)
            epsilon_f = vals.get("epsilon_f", 0.9)
            epsilon_b = vals.get("epsilon_b", 0.8)
            a_area = vals.get("a_area", 1.0)
            z = vals.get("z", 1.0)
            p_max = vals.get("p_max", 100.0)
            t_b = vals.get("t_b", 300.0)

            roots = tempatureFront(
                fourth, tau, t_wall, k, epsilon_f, epsilon_b, a_area, z, p_max, t_b
            )

            if not roots:
                self.result_label.configure(text="No valid positive\nreal roots found.")
            else:
                lines = ["RESULT:"]
                for i, r in enumerate(roots):
                    lines.append(f"  Tf[{i}] = {r:.4f} K")
                    lines.append(f"       = {r - 273.15:.2f} C")
                self.result_label.configure(text="\n".join(lines))

            self._update_plot(
                fourth, tau, t_wall, k, epsilon_f, epsilon_b, a_area, z, p_max, t_b
            )

        except ValueError as ex:
            messagebox.showerror("Input Error", f"Invalid input:\n{ex}")
        except Exception as ex:
            messagebox.showerror("Calculation Error", f"Error:\n{ex}")

    def _update_plot(
        self, fourth, tau, t_wall, k, epsilon_f, epsilon_b, a_area, z, p_max, t_b
    ):
        self.ax.clear()
        self._style_axes(self.ax)

        t_b_range = np.linspace(max(10, t_b * 0.5), t_b * 1.5, 120)
        tf_values = []
        tb_valid = []

        for tb_i in t_b_range:
            try:
                res = tempatureFront(
                    fourth, tau, t_wall, k, epsilon_f, epsilon_b, a_area, z, p_max, tb_i
                )
                if res:
                    tf_values.append(res[0])
                    tb_valid.append(tb_i)
            except Exception:
                pass

        if tf_values:
            self.ax.plot(
                tb_valid, tf_values, color="#0055ff", linewidth=1.5, label="T_f"
            )

        self.ax.set_xlabel("T_b [K]", fontsize=10)
        self.ax.set_ylabel("T_f [K]", fontsize=10)
        mode = "Full (Ferrari)" if fourth else "Simplified"
        self.ax.set_title(f"Tf vs Tb [{mode}]", fontsize=10)
        self.ax.legend(
            fontsize=9, facecolor=WIN_LITE, edgecolor=WIN_DARK, labelcolor=TXT
        )
        self._style_axes(self.ax)
        self.canvas.draw()


if __name__ == "__main__":
    app = ThermalApp()
    app.mainloop()
