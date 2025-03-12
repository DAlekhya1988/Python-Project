import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import csv
import numpy as np


class Diagram:
    """
    Basisklasse für alle Diagramme in der Anwendung.
    Diese Klasse definiert die grundlegende Funktionalität, die alle Diagrammtypen gemeinsam haben.
    """

    def __init__(self, parent_frame, app_instance):
        """
        Initialisiert ein Basisdiagramm.

        Args:
            parent_frame: Der Frame, in dem das Diagramm angezeigt wird
            app_instance: Die Instanz der Hauptanwendung für Datenzugriff
        """
        self.parent = parent_frame
        self.app = app_instance
        self.df = None
        self.highlight_country = None
        self.countries_by_continent = {}

        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack_forget()

        self.hint_label = ttk.Label(self.parent,
                                    text="Bitte laden Sie eine CSV-Datei, um das Diagramm anzuzeigen.",
                                    font=("Arial", 12))
        self.hint_label.pack(expand=True)

        self.set_diagram_background('#FFF8E1')

    def set_data(self, df):
        """
        Setzt die Daten für das Diagramm.

        Args:
            df: Der DataFrame mit den zu visualisierenden Daten
        """
        self.df = df
        self.update()

    def show(self):
        """
        Zeigt das Diagramm an.
        """
        if self.canvas_widget.winfo_ismapped() == 0:
            self.hint_label.pack_forget()
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)

    def update(self):
        """
        Aktualisiert das Diagramm. Muss von Unterklassen implementiert werden.
        """
        if self.df is None:
            return

        self.show()

    def save(self, filepath):
        """
        Speichert das Diagramm als Bilddatei.

        Args:
            filepath: Der Pfad, unter dem das Bild gespeichert werden soll
        """
        if self.df is None:
            return False

        try:
            original_size = self.figure.get_size_inches()
            self.figure.set_size_inches(12, 8)

            self.figure.savefig(
                filepath,
                dpi=300,
                bbox_inches='tight',
                pad_inches=0.5
            )

            self.figure.set_size_inches(*original_size)
            return True

        except Exception as e:
            print(f"Fehler beim Speichern des Diagramms: {e}")
            return False

    def set_diagram_background(self, color='#FFFACD'):
        """
        Ändert nur die Hintergrundfarbe des Diagramms.

        Args:
            color: Hex-Farbcode für den Hintergrund (Standard: Hellgelb)
        """
        self.figure.patch.set_facecolor(color)

        self.ax.set_facecolor(color)

        self.canvas_widget.configure(background=color)

        self.canvas.draw()


class BarDiagram(Diagram):
    """
    Klasse für Balkendiagramme, erbt von der Basisklasse Diagram.
    """

    def __init__(self, parent_frame, app_instance):
        """
        Initialisiert ein Balkendiagramm.

        Args:
            parent_frame: Der Frame, in dem das Diagramm angezeigt wird
            app_instance: Die Instanz der Hauptanwendung für Datenzugriff
        """
        super().__init__(parent_frame, app_instance)

        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="Kontinentauswahl:").pack(side=tk.LEFT, padx=(0, 10))
        self.continent_var = tk.StringVar()
        self.continent_combo = ttk.Combobox(control_frame, textvariable=self.continent_var,state="disabled", width=15)
        self.continent_combo.pack(side=tk.LEFT)
        self.continent_combo.bind("<<ComboboxSelected>>", self.on_continent_selected)
        ttk.Label(control_frame, text="  ").pack(side=tk.LEFT)

        ttk.Label(control_frame, text="Länder:").pack(side=tk.LEFT, padx=(10, 10))
        self.country_var = tk.StringVar()
        self.country_combo = ttk.Combobox(control_frame, textvariable=self.country_var,state="disabled", width=20)
        self.country_combo.pack(side=tk.LEFT)
        self.country_combo.bind("<<ComboboxSelected>>", self.on_country_selected)

        self.highlight_country = None

    def set_data(self, df):
        """
        Setzt die Daten und initialisiert die Comboboxen.

        Args:
            df: Der DataFrame mit den zu visualisierenden Daten
        """
        self.df = df
        if df is not None:
            continents = sorted(df['Continent'].unique())
            self.continent_combo.config(values=["Alle"] + continents, state="readonly")
            self.continent_combo.current(0)

            self.countries_by_continent = {"Alle": sorted(df['Entity'].unique())}
            for continent in continents:
                countries = sorted(df[df['Continent'] == continent]['Entity'].unique())
                self.countries_by_continent[continent] = countries

            self.country_combo.config(values=["Alle Länder"] + self.countries_by_continent["Alle"],
                                      state="readonly")
            self.country_combo.current(0)

        self.update()

    def on_country_selected(self, event=None):
        """
        Wird aufgerufen, wenn ein Land ausgewählt wurde.

        Args:
            event: Das Event-Objekt (optional)
        """
        selected_country = self.country_var.get()

        if selected_country == "Alle Länder":
            self.highlight_country = None
        else:
            self.highlight_country = selected_country

        self.update()

    def on_continent_selected(self, event=None):
        """
        Wird aufgerufen, wenn ein Kontinent ausgewählt wurde.

        Args:
            event: Das Event-Objekt (optional)
        """
        selected_continent = self.continent_var.get()

        if selected_continent in self.countries_by_continent:
            countries = self.countries_by_continent[selected_continent]
            self.country_combo.config(values=["Alle Länder"] + countries)
            self.country_combo.current(0)

        self.highlight_country = None
        self.update()

    def update(self):
        """
        Aktualisiert das Balkendiagramm basierend auf den ausgewählten Filtern.
        """
        if self.df is None:
            return

        super().update()

        self.set_diagram_background('#FFF8E1')

        selected_continent = self.continent_var.get()

        if selected_continent == "Alle":
            filtered_df = self.df
            title = "Einschulungsrate auf allen Kontinenten"
        else:
            filtered_df = self.df[self.df['Continent'] == selected_continent]
            title = f"Einschulungsrate - {selected_continent}"

        self.ax.clear()

        filtered_df = filtered_df.sort_values(
            by="Combined total net enrolment rate, primary, both sexes",
            ascending=False
        )

        countries = filtered_df['Entity'].values
        values = filtered_df["Combined total net enrolment rate, primary, both sexes"].values
        years = filtered_df['Year'].values

        if filtered_df.empty:
            self.ax.text(0.5, 0.5, f"Keine Daten für {selected_continent} vorhanden",
                         horizontalalignment='center', fontsize=14)
            self.canvas.draw()
            return

        colors = ['orange' if self.highlight_country == country else 'skyblue' for country in countries]

        bars = self.ax.bar(countries, values, color=colors)

        # Add year labels below bars
        for i, bar in enumerate(bars):
            self.ax.text(bar.get_x() + bar.get_width() / 2, 5,
                         f"{int(years[i])}", ha='center', va='bottom',
                         color='black', rotation=90, fontsize=8)

        self.ax.set_title(title, fontsize=14)
        self.ax.set_xlabel('Länder', fontsize=12)
        self.ax.set_ylabel('Einschulungsrate (%)', fontsize=12)
        self.ax.set_ylim(0, 105)

        # Add value labels above bars
        for bar in bars:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width() / 2., height + 1,
                         f'{height:.2f}%', ha='center', va='bottom', fontsize=8)
        # rotates x-axis labels
        plt.xticks(rotation=45, ha='right', fontsize=10)

        self.figure.tight_layout()
        self.canvas.draw()


class ScatterPlot(Diagram):
    """
    Klasse für Streudiagramme, erbt von der Basisklasse Diagram.
    """

    def __init__(self, parent_frame, app_instance):
        """
        Initialisiert ein Streudiagramm.
        Args:
            parent_frame: Der Frame, in dem das Diagramm angezeigt wird
            app_instance: Die Instanz der Hauptanwendung für Datenzugriff
        """
        super().__init__(parent_frame, app_instance)
        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="Kontinentauswahl:").pack(side=tk.LEFT, padx=(0, 10))
        self.continent_var = tk.StringVar()
        self.continent_combo = ttk.Combobox(control_frame, textvariable=self.continent_var,
                                            state="disabled", width=15)
        self.continent_combo.pack(side=tk.LEFT)
        self.continent_combo.bind("<<ComboboxSelected>>", self.on_continent_selected)

        ttk.Label(control_frame, text=" ").pack(side=tk.LEFT)

        ttk.Label(control_frame, text="Länder:").pack(side=tk.LEFT, padx=(10, 10))
        self.country_var = tk.StringVar()
        self.country_combo = ttk.Combobox(control_frame, textvariable=self.country_var,
                                          state="disabled", width=20)
        self.country_combo.pack(side=tk.LEFT)
        self.country_combo.bind("<<ComboboxSelected>>", self.on_country_selected)

        self.highlight_country = None
        self.countries_by_continent = {}

    def set_data(self, df):
        """
        Setzt die Daten und initialisiert die Comboboxen.
        Args:
            df: Der DataFrame mit den zu visualisierenden Daten
        """
        self.df = df
        if df is not None:
            continents = sorted(df['Continent'].unique())
            self.continent_combo.config(values=["Alle"] + continents, state="readonly")
            self.continent_combo.current(0)

            self.countries_by_continent = {"Alle": sorted(df['Entity'].unique())}
            for continent in continents:
                countries = sorted(df[df['Continent'] == continent]['Entity'].unique())
                self.countries_by_continent[continent] = countries

            self.country_combo.config(values=["Alle Länder"] + self.countries_by_continent["Alle"],
                                      state="readonly")
            self.country_combo.current(0)
            self.update()

    def update(self):
        """
        Aktualisiert das Streudiagramm basierend auf den ausgewählten Filtern.
        """
        if self.df is None:
            return

        super().update()

        self.set_diagram_background('#FFF8E1')
        self.canvas.draw()

        selected_continent = self.continent_var.get()
        selected_country = self.country_var.get()

        if selected_continent == "Alle":
            filtered_df = self.df
            title = "Einschulungsrate im Zeitverlauf - Alle Kontinente"
        else:
            filtered_df = self.df[self.df['Continent'] == selected_continent]
            title = f"Einschulungsrate im Zeitverlauf - {selected_continent}"

        if selected_country != "Alle Länder":
            filtered_df = filtered_df[filtered_df['Entity'] == selected_country]
            title = f"Einschulungsrate im Zeitverlauf - {selected_country}"

        self.ax.clear()

        if filtered_df.empty:
            self.ax.text(0.5, 0.5, f"Keine Daten für die ausgewählten Filter vorhanden",
                         horizontalalignment='center', fontsize=14)
            self.canvas.draw()
            return

        if selected_country != "Alle Länder":
            years = filtered_df['Year'].values
            values = filtered_df["Combined total net enrolment rate, primary, both sexes"].values
            self.ax.plot(years, values, 'o-', color='blue', markersize=6)

            for x, y in zip(years, values):
                self.ax.text(x, y + 1, f"{y:.1f}%", ha='center', va='bottom', fontsize=8)

        else:
            countries = filtered_df['Entity'].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(countries)))

            for i, country in enumerate(countries):
                country_data = filtered_df[filtered_df['Entity'] == country]
                years = country_data['Year'].values
                values = country_data["Combined total net enrolment rate, primary, both sexes"].values

                if len(years) > 0:
                    self.ax.scatter(years, values, color=colors[i], alpha=0.7, label=country)

            if len(countries) > 1 and len(countries) <= 15:
                self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                               ncol=min(5, len(countries)), fontsize=8)

        self.ax.set_title(title, fontsize=14)
        self.ax.set_xlabel('Jahr', fontsize=12)
        self.ax.set_ylabel('Einschulungsrate (%)', fontsize=12)
        self.ax.set_ylim(0, 105)
        self.ax.grid(True, linestyle='--', alpha=0.7)

        self.ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

        self.figure.tight_layout()
        self.canvas.draw()

    def on_continent_selected(self, event=None):
        """
        Wird aufgerufen, wenn ein Kontinent ausgewählt wurde.

        Args:
            event: Das Event-Objekt (optional)
        """
        selected_continent = self.continent_var.get()

        if selected_continent in self.countries_by_continent:
            countries = self.countries_by_continent[selected_continent]
            self.country_combo.config(values=["Alle Länder"] + countries)
            self.country_combo.current(0)

        self.highlight_country = None
        self.update()

    def on_country_selected(self, event=None):
        """
        Wird aufgerufen, wenn ein Land ausgewählt wurde.

        Args:
            event: Das Event-Objekt (optional)
        """
        selected_country = self.country_var.get()

        if selected_country == "Alle Länder":
            self.highlight_country = None
        else:
            self.highlight_country = selected_country

        self.update()


class PieDiagram(Diagram):
    """
    Klasse für Kreisdiagramme, erbt von der Basisklasse Diagram.
    """

    def __init__(self, parent_frame, app_instance):
        """
        Initialisiert ein Kreisdiagramm.

        Args:
            parent_frame: Der Frame, in dem das Diagramm angezeigt wird
            app_instance: Die Instanz der Hauptanwendung für Datenzugriff
        """
        super().__init__(parent_frame, app_instance)

        self.figure.set_size_inches(8, 8)

        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="Datenvisualisierung:").pack(side=tk.LEFT, padx=(0, 10))

        self.chart_type_var = tk.StringVar()
        self.chart_options = [
            "Durchschnittliche Einschulungsrate nach Kontinent",
            "Verteilung nach Einschulungsratenbereichen",
            "Verteilung der Daten nach Jahr"
        ]
        self.chart_type_var.set(self.chart_options[0])

        self.chart_type_menu = ttk.Combobox(
            control_frame,
            textvariable=self.chart_type_var,
            values=self.chart_options,
            state="readonly",
            width=40
        )
        self.chart_type_menu.pack(side=tk.LEFT, padx=5)

        self.chart_type_menu.bind("<<ComboboxSelected>>", self.on_chart_type_selected)

        self.range_frame = ttk.Frame(control_frame)
        self.range_frame.pack(side=tk.LEFT, padx=(15, 0))

        ttk.Label(self.range_frame, text="Minimaler Bereich:").pack(side=tk.LEFT)
        self.min_var = tk.StringVar(value="60")
        self.min_entry = ttk.Spinbox(
            self.range_frame,
            from_=0,
            to=100,
            increment=5,
            textvariable=self.min_var,
            width=5
        )
        self.min_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.range_frame, text="Schrittgröße:").pack(side=tk.LEFT)
        self.step_var = tk.StringVar(value="10")
        self.step_entry = ttk.Spinbox(
            self.range_frame,
            from_=5,
            to=25,
            increment=5,
            textvariable=self.step_var,
            width=5
        )
        self.step_entry.pack(side=tk.LEFT, padx=5)

        self.update_btn = ttk.Button(
            self.range_frame,
            text="Aktualisieren",
            command=self.update
        )
        self.update_btn.pack(side=tk.LEFT, padx=5)

        self.range_frame.pack_forget()

    def on_chart_type_selected(self, event=None):
        """
        Wird aufgerufen, wenn ein Diagrammtyp ausgewählt wurde.

        Args:
            event: Das Event-Objekt (optional)
        """
        chart_type = self.chart_type_var.get()

        if chart_type == "Verteilung nach Einschulungsratenbereichen":
            self.range_frame.pack(side=tk.LEFT, padx=(15, 0))
        else:
            self.range_frame.pack_forget()

        self.update()

    def update(self):
        """
        Aktualisiert das Kreisdiagramm basierend auf der ausgewählten Option.
        """
        if self.df is None:
            return

        super().update()

        self.set_diagram_background('#FFF8E1')

        self.canvas.draw()

        self.ax.clear()

        chart_type = self.chart_type_var.get()

        if chart_type == "Durchschnittliche Einschulungsrate nach Kontinent":
            self.create_continent_avg_chart()
        elif chart_type == "Verteilung nach Einschulungsratenbereichen":
            self.create_range_distribution_chart()
        elif chart_type == "Verteilung der Daten nach Jahr":
            self.create_year_distribution_chart()

        self.canvas.draw()

    def create_continent_avg_chart(self):
        """
        Erstellt ein Kreisdiagramm, das die durchschnittliche Einschulungsrate
        nach Kontinenten darstellt.
        """
        continent_avg = self.df.groupby('Continent')['Combined total net enrolment rate, primary, both sexes'].mean()

        continent_avg = continent_avg.sort_values(ascending=False)

        values = continent_avg.values
        labels = continent_avg.index

        colors = plt.cm.Paired(np.arange(len(values)) / len(values))
        explode = [0.1 if i == 0 else 0 for i in range(len(values))]

        wedges, texts, autotexts = self.ax.pie(
            values,
            explode=explode,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors,
            shadow=True,
            startangle=90
        )

        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color('white')

        self.ax.set_title("Durchschnittliche Einschulungsrate nach Kontinent")
        self.ax.axis('equal')

    def create_range_distribution_chart(self):
        """
        Erstellt ein Kreisdiagramm, das die Verteilung der Einschulungsraten
        in definierten Bereichen darstellt.
        """
        try:
            min_val = float(self.min_var.get())
            step_val = float(self.step_var.get())

            min_val = max(0, min(100, min_val))
            step_val = max(5, min(25, step_val))

            max_val = 100
            bins = [min_val]
            current = min_val

            while current < max_val:
                current += step_val
                current = min(current, max_val)
                bins.append(current)

            range_labels = [f"{bins[i]:.0f}%-{bins[i + 1]:.0f}%" for i in range(len(bins) - 1)]

            enrolment_col = 'Combined total net enrolment rate, primary, both sexes'
            binned_data = pd.cut(
                self.df[enrolment_col],
                bins=bins,
                labels=range_labels,
                include_lowest=True
            )

            range_counts = binned_data.value_counts().sort_index()

            if len(range_counts) == 0:
                self.ax.text(0.5, 0.5, "Keine Daten in den angegebenen Bereichen",
                             ha='center', va='center', fontsize=12)
                return

            values = range_counts.values
            labels = range_counts.index

            cmap = plt.cm.Greens
            colors = cmap(np.linspace(0.3, 0.9, len(values)))

            wedges, texts, autotexts = self.ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors,
                shadow=True,
                startangle=90
            )

            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_color('white')

            self.ax.set_title(
                f"Verteilung der Länder nach Einschulungsrate (Minimum: {min_val}%, Schritte: {step_val}%)")
            self.ax.axis('equal')

        except Exception as e:
            self.ax.text(0.5, 0.5, f"Fehler bei der Diagrammerstellung:\n{str(e)}",
                         ha='center', va='center', fontsize=10)

    def create_year_distribution_chart(self):
        """
        Erstellt ein Kreisdiagramm, das die Verteilung der Daten nach Jahren darstellt.
        """
        year_counts = self.df['Year'].value_counts().sort_index()

        values = year_counts.values
        labels = [str(int(year)) for year in year_counts.index]

        colors = plt.cm.viridis(np.linspace(0, 0.9, len(values)))

        wedges, texts, autotexts = self.ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors,
            shadow=True,
            startangle=90
        )

        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color('white')

        self.ax.set_title("Verteilung der Daten nach Erhebungsjahr")
        self.ax.axis('equal')


class PlotterDiagram(Diagram):
    """
    Klasse für Kontinentendiagramme, erbt von der Basisklasse Diagram.
    Zeigt Einschulungsraten nach Kontinenten, basierend auf dem Plotter-Code.
    """

    def __init__(self, parent_frame, app_instance):
        """
        Initialisiert ein Kontinentendiagramm.
        Args:
            parent_frame: Der Frame, in dem das Diagramm angezeigt wird
            app_instance: Die Instanz der Hauptanwendung für Datenzugriff
        """
        super().__init__(parent_frame, app_instance)

        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="Darstellung der Einschulungsraten nach Kontinenten").pack(side=tk.LEFT,
                                                                                                 padx=(0, 10))

        self.info_label = ttk.Label(control_frame,
                                    text="Separate Diagramme für jeden Kontinent werden angezeigt.")
        self.info_label.pack(side=tk.LEFT, padx=10)

    def update(self):
        """
        Aktualisiert die Diagramme für Kontinente basierend auf den Daten.
        """
        if self.df is None:
            return

        super().update()

        self.set_diagram_background('#FFF8E1')

        plt.close(self.figure)
        self.ax.clear()

        ents = self.df['Entity'].values
        conts = self.df['Continent'].values
        years = self.df['Year'].values
        rates = self.df['Combined total net enrolment rate, primary, both sexes'].values

        unique_continents = sorted(list(set(conts)))

        plt.close(self.figure)

        self.figure, axes = plt.subplots(len(unique_continents), 1,
                                         figsize=(10, 4 * len(unique_continents)))

        if len(unique_continents) == 1:
            axes = [axes]

        for i, continent in enumerate(unique_continents):
            continent_indices = [j for j, c in enumerate(conts) if c == continent]
            continent_years = [years[j] for j in continent_indices]
            continent_rates = [rates[j] for j in continent_indices]
            continent_ents = [ents[j] for j in continent_indices]

            unique_entities = sorted(list(set(continent_ents)))

            axes[i].grid(True, which="both")
            axes[i].set_title(f"Einschulung - {continent}")
            axes[i].set_xlabel("Jahr")
            axes[i].set_ylabel("Einschulungsrate (%)")
            axes[i].set_xlim(1820, 2025)
            axes[i].set_ylim(0, 100)

            colors = plt.cm.tab20(range(len(unique_entities)))

            for j, entity in enumerate(unique_entities):
                entity_indices = [k for k, e in enumerate(continent_ents) if e == entity]
                entity_years = [continent_years[k] for k in entity_indices]
                entity_rates = [continent_rates[k] for k in entity_indices]

                axes[i].scatter(entity_years, entity_rates, label=entity,
                                color=colors[j % len(colors)])

                if len(entity_years) > 1:
                    entity_data = sorted(zip(entity_years, entity_rates))
                    sorted_years, sorted_rates = zip(*entity_data)
                    axes[i].plot(sorted_years, sorted_rates,
                                 color=colors[j % len(colors)], alpha=0.7)

            if len(unique_entities) <= 15:
                axes[i].legend(loc='best', fontsize='small')
            else:
                axes[i].text(0.02, 0.98, f"{len(unique_entities)} Länder",
                             transform=axes[i].transAxes, fontsize=10,
                             verticalalignment='top')

        self.figure.tight_layout()

        if hasattr(self, 'canvas_widget'):
            self.canvas_widget.pack_forget()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        self.show()


class EinschulungsApp:
    """
    Hauptanwendungsklasse für die Visualisierung von Einschulungsraten nach Kontinenten.
    Ermöglicht das Laden von CSV-Dateien, Filtern nach Kontinenten und Ländern,
    sowie die Konvertierung in das JSON-Format.
    """

    def __init__(self, root):
        """
        Initialisiert die Anwendung.

        Args:
            root: Das Tkinter-Hauptfenster
        """
        self.root = root
        self.root.title("Einschulungsrate nach Kontinenten")
        self.root.geometry("900x700")

        pale_yellow = "#FFFACD"
        self.root.configure(background=pale_yellow)

        self.style = ttk.Style()
        self.style.configure("TFrame", background=pale_yellow)
        self.style.configure("TLabel", background=pale_yellow)
        self.style.configure("TButton", background=pale_yellow)
        self.style.configure("TNotebook", background=pale_yellow)
        self.style.configure("TNotebook.Tab", background=pale_yellow)

        self.df = None
        self.file_path = None
        self.create_menu()
        self.create_notebook()

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.create_tabs()

    def create_tabs(self):
        """
        Erstellt alle Tabs mit ihren jeweiligen Inhalten.
        """
        tab1_content_frame = ttk.Frame(self.tab1)
        tab1_content_frame.pack(fill=tk.BOTH, expand=True)

        overview_frame = ttk.Frame(tab1_content_frame)
        overview_frame.pack(fill=tk.X, padx=10, pady=10)

        overview_text = """
        Einschulungsraten-Analyse

        Diese Anwendung wurde entwickelt, um globale Bildungsdaten zu visualisieren und zu analysieren, mit besonderem Fokus auf die Einschulungsraten in verschiedenen Ländern und Kontinenten.

        Zweck der Anwendung

        Mit diesem Tool können Bildungsexperten, Forscher und politische Entscheidungsträger:

        - Die Einschulungsraten verschiedener Länder visuell vergleichen
        - Regionale Unterschiede in der Bildungsbeteiligung identifizieren
        - Länder mit besonders hohen oder niedrigen Einschulungsraten erkennen
        - Durch Kontinentfilterung geografische Muster analysieren
        - Spezifische Länder hervorheben, um sie genauer zu untersuchen

        Nutzungsmöglichkeiten

        Das Balkendiagramm bietet eine intuitive Darstellung der Einschulungsraten, wobei die Länder nach ihren Werten sortiert sind. Die Filteroptionen erlauben es Ihnen:

        - Zwischen verschiedenen Kontinenten zu wechseln
        - Einzelne Länder für detailliertere Betrachtung hervorzuheben
        - Die genauen Prozentwerte und das entsprechende Erhebungsjahr jedes Landes zu sehen

        Vorteile der visuellen Datenanalyse

        Diese Visualisierung ermöglicht es:

        - Komplexe statistische Daten auf einen Blick zu erfassen
        - Bildungstrends schnell zu identifizieren
        - Fundierte Entscheidungen auf Basis globaler Vergleichsdaten zu treffen
        - Bildungserfolge und -herausforderungen in verschiedenen Regionen zu erkennen

        Laden Sie eine CSV-Datei mit Einschulungsdaten, um mit der Analyse zu beginnen. Die Visualisierung wird automatisch aktualisiert, wenn Sie die Filter anpassen.
        """

        overview_text_scroll = tk.Scrollbar(overview_frame)
        overview_text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        cream_color = "#FFF8E1"
        overview_text_widget = tk.Text(overview_frame, wrap=tk.WORD, height=30,
                                       font=("Arial", 10),
                                       yscrollcommand=overview_text_scroll.set,
                                       background=cream_color,
                                       highlightbackground=cream_color,
                                       borderwidth=0)

        overview_text_widget.insert(tk.END, overview_text)
        overview_text_widget.config(state=tk.DISABLED)
        overview_text_widget.pack(fill=tk.X, expand=True)
        overview_text_scroll.config(command=overview_text_widget.yview)

        self.bar_diagram = BarDiagram(self.tab2, self)

        self.scatter_plot = ScatterPlot(self.tab3, self)

        self.pie_diagram = PieDiagram(self.tab4, self)

        self.plotter_diagram = PlotterDiagram(self.tab5, self)

    def on_tab_changed(self, event):
        """
        Wird aufgerufen, wenn der Benutzer zwischen Tabs wechselt.
        """
        current_tab = self.notebook.select()
        current_tab_index = self.notebook.index(current_tab)

        if self.df is None:
            return

        if current_tab_index == 1:
            self.bar_diagram.update()
        elif current_tab_index == 2:
            self.scatter_plot.update()
        elif current_tab_index == 3:
            self.pie_diagram.update()
        elif current_tab_index == 4:
            self.plotter_diagram.update()

    def create_menu(self):
        """
        Erstellt die Menüleiste mit vier Menütabs: Datei, Tab2, Tab3 und Tab4.
        Das Datei-Menü enthält Optionen für Dateioperationen, während die anderen
        Tabs für zukünftige Erweiterungen reserviert sind.
        """
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Datei", menu=self.file_menu)
        self.file_menu.add_command(label="CSV-Datei öffnen", command=self.load_csv_file)
        self.file_menu.add_command(label="CSV-Datei speichern", command=self.save_csv_file)
        self.file_menu.add_command(label="In JSON konvertieren", command=self.convert_to_json)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Diagramm als Bild speichern", command=self.save_chart_as_image)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Beenden", command=self.root.destroy)

        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="Über", command=self.show_about)
        self.menubar.add_cascade(label="Hilfe", menu=help_menu)

    def show_about(self):
        """Zeigt Informationen über die Anwendung an."""
        messagebox.showinfo(
            "Über",
            "Grundschulbildungsraten Visualisierungstool\n\n"
            "Version 2.0\n"
            "Ein Tool zur Visualisierung von Grundschulbildungsraten weltweit.\n\n"
            "Erweiterung mit Diagrammen und Kontinentfilterung"
        )

    def create_notebook(self):
        """
        Erstellt das Notebook mit den vier Tabs.
        """
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab1 = ttk.Frame(self.notebook, style="TFrame")
        self.tab2 = ttk.Frame(self.notebook, style="TFrame")
        self.tab3 = ttk.Frame(self.notebook, style="TFrame")
        self.tab4 = ttk.Frame(self.notebook, style="TFrame")
        self.tab5 = ttk.Frame(self.notebook, style="TFrame")

        for tab in [self.tab1, self.tab2, self.tab3, self.tab4, self.tab5]:
            tab.configure(style="TFrame")

        self.notebook.add(self.tab1, text="Übersicht")
        self.notebook.add(self.tab2, text="Balkendiagramm")
        self.notebook.add(self.tab3, text="Streudiagramm")
        self.notebook.add(self.tab4, text="Kreisdiagramm")
        self.notebook.add(self.tab5, text="Kontinentendiagramm")

    def load_csv_file(self):
        """
        Lädt eine CSV-Datei über einen Dateiauswahl-Dialog und verarbeitet
        die Daten für die Anzeige.
        """
        file_path = filedialog.askopenfilename(
            title="CSV-Datei auswählen",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                cleaned_headers = [h.strip('"\' ') for h in headers]

            df = pd.read_csv(file_path, encoding='utf-8')

            if 'Entity' not in df.columns and 'Entity' in cleaned_headers:
                rename_dict = {col: clean for col, clean in zip(df.columns, cleaned_headers)}
                df = df.rename(columns=rename_dict)

            required_columns = ['Entity', 'Continent', 'Year',
                                'Combined total net enrolment rate, primary, both sexes']

            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                messagebox.showerror(
                    "Fehler",
                    f"Die Datei hat ein ungültiges Format. Folgende Spalten fehlen: {', '.join(missing_cols)}\n\n"
                    f"Vorhandene Spalten: {', '.join(df.columns)}"
                )
                return

            self.df = df
            self.file_path = file_path

            if self.df is not None:
                self.bar_diagram.set_data(self.df)
                self.scatter_plot.set_data(self.df)
                self.pie_diagram.set_data(self.df)
                self.plotter_diagram.set_data(self.df)

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der CSV-Datei:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def save_csv_file(self):
        """
        Speichert die aktuell geladenen Daten als CSV-Datei über einen
        Dateiauswahl-Dialog.
        """
        if self.df is None:
            messagebox.showwarning("Warnung", "Keine Daten zum Speichern vorhanden.")
            return

        if self.file_path:
            default_name = os.path.basename(self.file_path)
        else:
            default_name = "einschulungs_daten.csv"

        csv_path = filedialog.asksaveasfilename(
            title="CSV-Datei speichern",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )

        if not csv_path:
            return

        try:
            self.df.to_csv(csv_path, index=False, encoding='utf-8')
            messagebox.showinfo("Erfolg", f"Datei erfolgreich gespeichert:\n{csv_path}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern der CSV-Datei:\n{str(e)}")

    def save_chart_as_image(self):
        """
        Speichert das aktuelle Diagramm als Bilddatei (PNG, JPG, PDF, SVG).
        """
        if self.df is None:
            messagebox.showwarning("Warnung", "Keine Daten zum Speichern vorhanden.")
            return

        current_tab_index = self.notebook.index(self.notebook.select())

        if current_tab_index == 1:
            diagram = self.bar_diagram
        elif current_tab_index == 2:
            diagram = self.scatter_plot
        elif current_tab_index == 3:
            diagram = self.pie_diagram
        else:
            messagebox.showwarning("Warnung", "In diesem Tab gibt es kein Diagramm zum Speichern.")
            return

        default_name = "diagramm.png"
        if self.file_path:
            default_name = os.path.splitext(os.path.basename(self.file_path))[0] + "_diagramm.png"

        image_path = filedialog.asksaveasfilename(
            title="Diagramm als Bild speichern",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[
                ("PNG-Dateien", "*.png"),
                ("JPEG-Dateien", "*.jpg *.jpeg"),
                ("PDF-Dateien", "*.pdf"),
                ("SVG-Dateien", "*.svg"),
                ("Alle Dateien", "*.*")
            ]
        )

        if not image_path:
            return

        success = diagram.save(image_path)

        if success:
            messagebox.showinfo("Erfolg", f"Diagramm erfolgreich gespeichert als:\n{image_path}")
        else:
            messagebox.showerror("Fehler", "Fehler beim Speichern des Diagramms.")

    def convert_to_json(self):
        """
        Konvertiert die geladenen CSV-Daten in das JSON-Format und
        speichert sie über einen Dateiauswahl-Dialog.
        """
        if self.df is None or self.file_path is None:
            messagebox.showwarning("Warnung", "Keine Daten zum Konvertieren vorhanden.")
            return

        default_name = os.path.splitext(os.path.basename(self.file_path))[0] + ".json"
        json_path = filedialog.asksaveasfilename(
            title="JSON-Datei speichern",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*")]
        )

        if not json_path:
            return

        try:
            json_str = self.df.to_json(orient="records", indent=4)

            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

            messagebox.showinfo("Erfolg", f"Datei erfolgreich als JSON gespeichert:\n{json_path}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei der Konvertierung nach JSON:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = EinschulungsApp(root)
    root.mainloop()
