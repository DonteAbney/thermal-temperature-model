import csv
import math
import cmath
from dataclasses import dataclass
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.constants import sigma as SIGMA

REAL_TOL = 1e-7
ZERO_TOL = 1e-14
APP_FONT = "DejaVu Sans"


@dataclass
class ModelInputs:
    tau: float
    area: float
    k: float
    eps_f: float
    eps_b: float
    tb: float
    pmax: float
    twall: float
    sample_step: float


def app_font(size, weight=None):
    return ctk.CTkFont(family=APP_FONT, size=size, weight=weight)


def real_cuberoot(value):
    if value >= 0:
        return value ** (1.0 / 3.0)
    return -((-value) ** (1.0 / 3.0))


def is_real_nonnegative(value):
    return abs(value.imag) <= REAL_TOL and value.real >= -REAL_TOL


def quadratic_roots(a, b, c):
    disc = complex(b * b - 4.0 * a * c)
    root_disc = cmath.sqrt(disc)
    return [(-b + root_disc) / (2.0 * a), (-b - root_disc) / (2.0 * a)]


def cardano_y_candidates(q, r):
    disc = (q**4) / 4.0 - (64.0 * r**3) / 27.0

    if disc >= 0:
        sqrt_disc = math.sqrt(disc)
        y = real_cuberoot((q**2) / 2.0 + sqrt_disc) + real_cuberoot(
            (q**2) / 2.0 - sqrt_disc
        )
        return [y]

    p = -4.0 * r
    cubic_q = -(q**2)

    if p < 0:
        inner = (3.0 * cubic_q / (2.0 * p)) * math.sqrt(-3.0 / p)
        inner = max(-1.0, min(1.0, inner))
        theta = math.acos(inner)
        radius = 2.0 * math.sqrt(-p / 3.0)
        return [radius * math.cos((theta - 2.0 * math.pi * i) / 3.0) for i in range(3)]

    sqrt_disc = cmath.sqrt(complex(disc))
    term_one = complex((q**2) / 2.0) + sqrt_disc
    term_two = complex((q**2) / 2.0) - sqrt_disc
    omega = complex(-0.5, math.sqrt(3.0) / 2.0)

    def cube_roots(z):
        if abs(z) <= ZERO_TOL:
            return [0j]
        base = z ** (1.0 / 3.0)
        return [base, base * omega, base * omega * omega]

    candidates = []
    for u in cube_roots(term_one):
        for v in cube_roots(term_two):
            y = u + v
            residual = y**3 - 4.0 * r * y - q**2
            if abs(residual) <= 1e-5 * max(1.0, abs(q**2), abs(r)):
                candidates.append(y.real if abs(y.imag) <= REAL_TOL else y)
    return candidates


def unique_sorted(values):
    clean = []
    for value in values:
        if not any(abs(value - existing) <= 1e-6 for existing in clean):
            clean.append(value)
    return sorted(clean)


def simplified_temperature(z_decimal, inputs):
    return inputs.tb + (2.0 * inputs.tau / (inputs.area * inputs.k)) * (
        z_decimal * inputs.pmax - SIGMA * inputs.area * inputs.eps_b * inputs.tb**4
    )


def quartic_dependance_temperature(
    z_decimal, inputs, reference_value=None, previous_value=None
):
    a = inputs.tau * SIGMA * (inputs.eps_b - inputs.eps_f) / inputs.k

    e = (
        inputs.tau * SIGMA * inputs.twall**4 * (inputs.eps_f - inputs.eps_b) / inputs.k
        + inputs.tau * z_decimal * inputs.pmax / (inputs.area * inputs.k)
        + inputs.tb
    )

    if abs(a) <= ZERO_TOL:
        root = e
        return max(0.0, root) if root >= -REAL_TOL else None

    q = -1.0 / a
    r = e / a

    roots = []
    for y_candidate in cardano_y_candidates(q, r):
        y = y_candidate.real if isinstance(y_candidate, complex) else y_candidate

        if y <= ZERO_TOL:
            continue

        sqrt_y = math.sqrt(y)
        positive_case_c = y / 2.0 + q / (2.0 * sqrt_y)
        negative_case_c = y / 2.0 - q / (2.0 * sqrt_y)

        possible_roots = []
        possible_roots.extend(quadratic_roots(1.0, -sqrt_y, positive_case_c))
        possible_roots.extend(quadratic_roots(1.0, sqrt_y, negative_case_c))

        for root in possible_roots:
            if is_real_nonnegative(root):
                real_root = 0.0 if abs(root.real) <= REAL_TOL else root.real
                residual = abs(a * real_root**4 - real_root + e)
                scale = max(1.0, abs(a * real_root**4), abs(real_root), abs(e))
                if residual <= 1e-6 * scale:
                    roots.append(real_root)

    roots = unique_sorted(roots)

    if not roots:
        return None

    if reference_value is not None and reference_value >= 0:
        return min(roots, key=lambda root: abs(root - reference_value))

    if previous_value is not None and previous_value >= 0:
        return min(roots, key=lambda root: abs(root - previous_value))

    return min(roots)


class ThermalSimulationApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Thermal Front Side Temperature Simulation")
        self.geometry("1280x760")
        self.minsize(1100, 680)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.method_var = ctk.StringVar(value="Simplified")
        self.rows = []
        self.canvas = None

        self.input_widgets = {}
        self.input_containers = {}

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_left_panel()
        self.build_right_panel()
        self.update_visible_inputs()
        self.calculate()

    def build_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, width=360, corner_radius=16)
        self.left_frame.grid(row=0, column=0, padx=18, pady=18, sticky="ns")
        self.left_frame.grid_propagate(False)
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.left_scroll_frame = ctk.CTkScrollableFrame(
            self.left_frame,
            width=330,
            corner_radius=16,
            fg_color="transparent",
        )
        self.left_scroll_frame.grid(row=0, column=0, sticky="nsew")

        title = ctk.CTkLabel(
            self.left_scroll_frame,
            text="Inputs and Controls",
            font=app_font(22, "bold"),
        )
        title.pack(padx=18, pady=(18, 10), anchor="w")

        fields = [
            ("tau_mm", "Thickness τ - mm", "1.0"),
            ("area_mm2", "Surface area A - mm^2", "100"),
            ("k", "Thermal conductivity k - W/(m*K)", "300"),
            ("eps_f", "Front emissivity ε_f", "1.00"),
            ("eps_b", "Back emissivity ε_b", "1.00"),
            ("tb", "Back temperature T_b - K", "300"),
            ("pmax", "Maximum power Pmax - W", "1000"),
            ("twall", "Wall temperature T_wall - K", "0"),
            ("sample_step", "Sample size Z - ratio", "0.1"),
        ]

        for key, label_text, default in fields:
            self.add_input_field(key, label_text, default)

        method_label = ctk.CTkLabel(
            self.left_scroll_frame,
            text="Method",
            font=app_font(14, "bold"),
        )
        method_label.pack(padx=18, pady=(14, 6), anchor="w")

        method_toggle = ctk.CTkSegmentedButton(
            self.left_scroll_frame,
            values=["Simplified", "Quartic Dependance"],
            variable=self.method_var,
            command=lambda _: self.on_method_change(),
            font=app_font(13),
        )
        method_toggle.pack(padx=18, pady=(0, 14), fill="x")

        calculate_button = ctk.CTkButton(
            self.left_scroll_frame,
            text="Calculate",
            height=38,
            command=self.calculate,
            font=app_font(14, "bold"),
        )
        calculate_button.pack(padx=18, pady=(4, 10), fill="x")

        export_chart_button = ctk.CTkButton(
            self.left_scroll_frame,
            text="Export Chart",
            height=36,
            command=self.export_chart,
            font=app_font(14),
        )
        export_chart_button.pack(padx=18, pady=6, fill="x")

        export_csv_button = ctk.CTkButton(
            self.left_scroll_frame,
            text="Export CSV",
            height=36,
            command=self.export_csv,
            font=app_font(14),
        )
        export_csv_button.pack(padx=18, pady=6, fill="x")

    def add_input_field(self, key, label_text, default):
        container = ctk.CTkFrame(self.left_scroll_frame, fg_color="transparent")
        container.pack(padx=18, pady=(8, 2), fill="x")

        label = ctk.CTkLabel(container, text=label_text, font=app_font(13))
        label.pack(anchor="w")

        entry = ctk.CTkEntry(container, height=32, font=app_font(13))
        entry.insert(0, default)
        entry.pack(pady=(2, 0), fill="x")

        self.input_widgets[key] = entry
        self.input_containers[key] = container

    def build_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, corner_radius=16)
        self.right_frame.grid(row=0, column=1, padx=(0, 18), pady=18, sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self.right_frame,
            text="Front Side Temperature vs Power Output",
            font=app_font(22, "bold"),
        )
        header.grid(row=0, column=0, padx=18, pady=(18, 4), sticky="w")

        self.figure = Figure(figsize=(7.2, 5.0), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.right_frame)
        self.canvas.get_tk_widget().grid(
            row=1, column=0, padx=18, pady=18, sticky="nsew"
        )

    def on_method_change(self):
        self.update_visible_inputs()
        self.update_plot()

    def update_visible_inputs(self):
        if self.method_var.get() == "Simplified":
            self.input_containers["twall"].pack_forget()
        else:
            self.input_containers["twall"].pack(
                before=self.input_containers["sample_step"],
                padx=18,
                pady=(8, 2),
                fill="x",
            )

    def read_inputs(self):
        try:
            tau_mm = float(self.input_widgets["tau_mm"].get())
            area_mm2 = float(self.input_widgets["area_mm2"].get())
            k = float(self.input_widgets["k"].get())
            eps_f = float(self.input_widgets["eps_f"].get())
            eps_b = float(self.input_widgets["eps_b"].get())
            tb = float(self.input_widgets["tb"].get())
            pmax = float(self.input_widgets["pmax"].get())
            twall = float(self.input_widgets["twall"].get())
            sample_step = float(self.input_widgets["sample_step"].get())
        except ValueError as exc:
            raise ValueError("All inputs must be numeric.") from exc

        if tau_mm <= 0:
            raise ValueError("Thickness must be greater than zero.")
        if area_mm2 <= 0:
            raise ValueError("Surface area must be greater than zero.")
        if k <= 0:
            raise ValueError("Thermal conductivity must be greater than zero.")
        if not 0 <= eps_f <= 1:
            raise ValueError("Front emissivity must be between 0 and 1.")
        if not 0 <= eps_b <= 1:
            raise ValueError("Back emissivity must be between 0 and 1.")
        if tb < 0 or twall < 0:
            raise ValueError("Temperatures cannot be negative Kelvin.")
        if pmax < 0:
            raise ValueError("Maximum power cannot be negative.")
        if sample_step <= 0:
            raise ValueError("Sample size must be greater than zero.")
        if sample_step > 100:
            raise ValueError("Sample size cannot be greater than 100 percent.")

        return ModelInputs(
            tau=tau_mm / 1000.0,
            area=area_mm2 / 1_000_000.0,
            k=k,
            eps_f=eps_f,
            eps_b=eps_b,
            tb=tb,
            pmax=pmax,
            twall=twall,
            sample_step=sample_step,
        )

    def calculate_rows(self, inputs):
        rows = []
        previous_quartic = None
        z_percent = 0.0

        while z_percent < 100.0:
            rounded_z = round(z_percent, 10)
            z_decimal = rounded_z / 100.0

            simplified = simplified_temperature(z_decimal, inputs)
            quartic = quartic_dependance_temperature(
                z_decimal,
                inputs,
                reference_value=simplified,
                previous_value=previous_quartic,
            )

            if quartic is not None:
                previous_quartic = quartic

            rows.append(
                {
                    "z_percent": rounded_z,
                    "z_decimal": z_decimal,
                    "simplified": simplified,
                    "quartic_dependance": quartic,
                }
            )

            z_percent += inputs.sample_step

        if not rows or rows[-1]["z_percent"] < 100.0:
            z_decimal = 1.0
            simplified = simplified_temperature(z_decimal, inputs)
            quartic = quartic_dependance_temperature(
                z_decimal,
                inputs,
                reference_value=simplified,
                previous_value=previous_quartic,
            )

            rows.append(
                {
                    "z_percent": 100.0,
                    "z_decimal": z_decimal,
                    "simplified": simplified,
                    "quartic_dependance": quartic,
                }
            )

        return rows

    def calculate(self):
        try:
            inputs = self.read_inputs()
            self.rows = self.calculate_rows(inputs)
            self.update_plot()

        except Exception as exc:
            messagebox.showerror("Input Error", str(exc))

    def update_plot(self):
        self.ax.clear()

        method = self.method_var.get()
        key = "simplified" if method == "Simplified" else "quartic_dependance"

        x_values = [row["z_percent"] for row in self.rows]
        y_values = [
            row[key] if row[key] is not None else float("nan") for row in self.rows
        ]

        self.ax.plot(x_values, y_values, linewidth=2)
        self.ax.set_title(f"{method} Method")
        self.ax.set_xlabel("Power Output Z in percent")
        self.ax.set_ylabel("Front Side Temperature Tf in K")
        self.ax.set_xlim(0, 100)
        self.ax.set_xticks([i for i in range(0, 101, 10)])
        self.ax.grid(True, alpha=0.35)

        finite_values = [value for value in y_values if math.isfinite(value)]
        if finite_values:
            y_min = min(finite_values)
            y_max = max(finite_values)
            if abs(y_max - y_min) <= ZERO_TOL:
                self.ax.set_ylim(y_min - 1.0, y_max + 1.0)
            else:
                padding = 0.08 * (y_max - y_min)
                self.ax.set_ylim(y_min - padding, y_max + padding)

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def export_chart(self):
        if not self.rows:
            messagebox.showwarning(
                "No Data", "Calculate the model before exporting a chart."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG image", "*.png"),
                ("PDF file", "*.pdf"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        self.figure.savefig(path, dpi=300, bbox_inches="tight")
        messagebox.showinfo("Export Complete", f"Chart saved to:\n{path}")

    def export_csv(self):
        if not self.rows:
            messagebox.showwarning(
                "No Data", "Calculate the model before exporting a CSV."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "Z percent",
                    "Z decimal",
                    "Simplified Tf K",
                    "Quartic Dependance Tf K",
                ]
            )

            for row in self.rows:
                writer.writerow(
                    [
                        f"{row['z_percent']:.10f}".rstrip("0").rstrip("."),
                        f"{row['z_decimal']:.10f}",
                        f"{row['simplified']:.10f}",
                        (
                            ""
                            if row["quartic_dependance"] is None
                            else f"{row['quartic_dependance']:.10f}"
                        ),
                    ]
                )

        messagebox.showinfo("Export Complete", f"CSV saved to:\n{path}")


if __name__ == "__main__":
    app = ThermalSimulationApp()
    app.mainloop()
