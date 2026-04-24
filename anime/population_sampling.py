from __future__ import annotations

import random
from dataclasses import dataclass

from manim import (
    BLUE,
    Circle,
    DashedLine,
    Dot,
    DOWN,
    FadeIn,
    FadeOut,
    GREEN,
    GrowFromPoint,
    Indicate,
    LEFT,
    Line,
    MathTex,
    ORANGE,
    RED,
    ReplacementTransform,
    RIGHT,
    Scene,
    Text,
    Transform,
    TransformFromCopy,
    UP,
    VGroup,
    Write,
)

HEIGHT_MIN = 155
HEIGHT_MAX = 195


@dataclass
class PersonRecord:
    pid: int
    height_cm: int
    sex: str


class PersonGlyph(VGroup):
    """Height-proportional person glyph, optionally colored by sex."""

    def __init__(self, record: PersonRecord, outer_scale: float = 1.0, color_by_sex: bool = False):
        super().__init__()

        frac = (record.height_cm - HEIGHT_MIN) / (HEIGHT_MAX - HEIGHT_MIN)
        torso_len = 0.18 + frac * 0.18
        arm_drop = torso_len * 0.38
        leg_len = 0.10 + frac * 0.10

        body_color = BLUE
        if color_by_sex:
            body_color = BLUE if record.sex == "M" else RED

        head = Circle(radius=0.09, color=body_color)
        torso = Line(head.get_bottom(), head.get_bottom() + DOWN * torso_len, color=body_color)
        arms = Line(
            torso.get_start() + LEFT * 0.10 + DOWN * arm_drop,
            torso.get_start() + RIGHT * 0.10 + DOWN * arm_drop,
            color=body_color,
        )
        leg_l = Line(torso.get_end(), torso.get_end() + LEFT * 0.08 + DOWN * leg_len, color=body_color)
        leg_r = Line(torso.get_end(), torso.get_end() + RIGHT * 0.08 + DOWN * leg_len, color=body_color)
        icon = VGroup(head, torso, arms, leg_l, leg_r)

        h_label = Text(str(record.height_cm), color=GREEN).scale(0.26)
        h_label.next_to(icon, RIGHT, buff=0.07)

        self.add(icon, h_label)
        self.scale(outer_scale)


class PopulationSampling(Scene):
    """Overall sample-mean distribution with population mean reference."""

    def _make_dot(self, mean_val: float) -> Dot:
        raw = int((mean_val - self.hist_min) / self.bin_width_cm)
        bin_idx = max(0, min(raw, self.n_bins - 1))
        count = self.bin_counts.get(bin_idx, 0)
        bx = self.hist_x_left + (bin_idx + 0.5) * self.bin_width_cm * self.ppc
        by = self.hist_baseline_y + self.dot_r + count * (2 * self.dot_r + 0.018)
        self.bin_counts[bin_idx] = count + 1
        self.total_dots += 1
        return Dot(point=[bx, by, 0], radius=self.dot_r, color=ORANGE)

    def _update_pct_labels(self, animate: bool = True) -> None:
        if self.total_dots == 0:
            return

        anims = []
        for bin_idx, count in self.bin_counts.items():
            pct = count / self.total_dots * 100
            bx = self.hist_x_left + (bin_idx + 0.5) * self.bin_width_cm * self.ppc
            by = self.hist_baseline_y + count * (2 * self.dot_r + 0.018) + self.dot_r + 0.12
            new_lbl = Text(f"{pct:.0f}%", color=ORANGE).scale(0.20)
            new_lbl.move_to([bx, by, 0])
            old = self.pct_labels.get(bin_idx)
            if old is None:
                self.pct_labels[bin_idx] = new_lbl
                if animate:
                    anims.append(FadeIn(new_lbl))
                else:
                    self.add(new_lbl)
            else:
                if animate:
                    anims.append(Transform(old, new_lbl))
                else:
                    old.become(new_lbl)

        if animate and anims:
            self.play(*anims, run_time=0.20)

    def show_sample_round(
        self,
        rng: random.Random,
        round_number: int,
        population_records: list[PersonRecord],
        sample_targets: list,
        sample_title: Text,
    ) -> None:
        sampled = rng.choices(population_records, k=5)

        new_title = Text(f"Sample {round_number}  (with replacement)").scale(0.34)
        new_title.move_to(sample_title)
        if round_number == 1:
            self.play(FadeIn(sample_title))
        else:
            self.play(Transform(sample_title, new_title))

        sample_box = VGroup()
        xi_labels = VGroup()
        for slot, rec in enumerate(sampled):
            source = self.person_glyphs[rec.pid - 1]
            copied = source.copy().scale(0.58).move_to(sample_targets[slot])
            self.play(Indicate(source, color=GREEN, scale_factor=1.10), run_time=0.20)
            self.play(TransformFromCopy(source, copied), run_time=0.30)
            sample_box.add(copied)
            lbl = MathTex(f"X_{{{slot + 1}}} = {rec.height_cm}", color=GREEN).scale(0.38)
            lbl.next_to(copied, RIGHT, buff=0.08)
            self.play(FadeIn(lbl), run_time=0.13)
            xi_labels.add(lbl)

        avg = sum(r.height_cm for r in sampled) / 5
        nums = " + ".join(f"X_{{{i + 1}}}" for i in range(5))
        formula = MathTex(r"\frac{" + nums + r"}{5} = " + f"{avg:.1f}").scale(0.40)
        formula.next_to(sample_box, DOWN, buff=0.20)
        self.play(Write(formula), run_time=0.80)

        xbar = MathTex(r"\bar{X}_{" + str(round_number) + r"} = " + f"{avg:.1f}", color=ORANGE).scale(0.48)
        xbar.move_to(formula)
        self.play(ReplacementTransform(formula, xbar), run_time=0.50)

        dot = self._make_dot(avg)
        self.play(TransformFromCopy(xbar, dot), run_time=0.45)
        self._update_pct_labels(animate=True)
        self.play(FadeOut(sample_box), FadeOut(xi_labels), FadeOut(xbar), run_time=0.38)

    def show_fast_round(self, rng: random.Random, population_records: list[PersonRecord]) -> None:
        sampled = rng.choices(population_records, k=5)
        avg = sum(r.height_cm for r in sampled) / 5
        dot = self._make_dot(avg)
        self.play(GrowFromPoint(dot, [dot.get_x(), self.hist_baseline_y, 0]), run_time=0.11)
        self._update_pct_labels(animate=False)

    def construct(self) -> None:
        rng = random.Random(2026)

        self.hist_baseline_y = -3.10
        self.hist_x_left = -5.80
        self.bin_width_cm = 2.0
        self.dot_r = 0.060
        self.bin_counts: dict[int, int] = {}
        self.total_dots = 0
        self.pct_labels: dict[int, Text] = {}

        n_population = 16
        population_records = [
            PersonRecord(
                pid=i + 1,
                height_cm=rng.randint(HEIGHT_MIN, HEIGHT_MAX),
                sex="M" if i < 8 else "F",
            )
            for i in range(n_population)
        ]
        pop_mean = sum(r.height_cm for r in population_records) / len(population_records)

        # Center histogram around population average height.
        half_range = 24.0
        self.hist_min = pop_mean - half_range
        self.hist_max = pop_mean + half_range
        self.ppc = 11.6 / (self.hist_max - self.hist_min)
        self.n_bins = int((self.hist_max - self.hist_min) / self.bin_width_cm)

        self.person_glyphs = VGroup(*[PersonGlyph(rec, outer_scale=0.92) for rec in population_records])
        self.person_glyphs.arrange_in_grid(rows=4, cols=4, buff=(0.28, 0.22))
        self.person_glyphs.move_to(LEFT * 3.4 + UP * 1.35)

        self.person_glyphs.scale(2.0).move_to(UP * 0.15)
        pop_label = Text(f"Population  (N = {n_population})", weight="BOLD").scale(0.52)
        pop_label.next_to(self.person_glyphs, UP, buff=0.22)
        self.play(FadeIn(pop_label), FadeIn(self.person_glyphs, lag_ratio=0.04, run_time=2.2))
        self.wait(1.0)

        ghost = self.person_glyphs.copy().scale(0.5).move_to(LEFT * 3.4 + UP * 1.35)
        small_label = Text(f"Population  (N={n_population})").scale(0.37)
        small_label.next_to(ghost, UP, buff=0.18)
        self.play(
            self.person_glyphs.animate.scale(0.5).move_to(LEFT * 3.4 + UP * 1.35),
            Transform(pop_label, small_label),
            run_time=1.20,
        )

        hist_x_right = self.hist_x_left + (self.hist_max - self.hist_min) * self.ppc
        x_axis = Line([self.hist_x_left, self.hist_baseline_y, 0], [hist_x_right, self.hist_baseline_y, 0])
        bin_lines = VGroup(
            *[
                DashedLine(
                    [self.hist_x_left + b * self.bin_width_cm * self.ppc, self.hist_baseline_y, 0],
                    [self.hist_x_left + b * self.bin_width_cm * self.ppc, self.hist_baseline_y + 2.30, 0],
                    dash_length=0.07,
                    dashed_ratio=0.40,
                    stroke_width=0.9,
                )
                for b in range(self.n_bins + 1)
            ]
        )
        ticks = VGroup()
        tick_lbl = VGroup()
        tick_start = int(self.hist_min // 5) * 5
        tick_end = int(self.hist_max // 5) * 5
        for val in range(tick_start, tick_end + 1, 5):
            tx = self.hist_x_left + (val - self.hist_min) * self.ppc
            ticks.add(Line([tx, self.hist_baseline_y - 0.09, 0], [tx, self.hist_baseline_y + 0.09, 0]))
            lbl = Text(str(val)).scale(0.20)
            lbl.move_to([tx, self.hist_baseline_y - 0.28, 0])
            tick_lbl.add(lbl)
        axis_title = Text("Sample mean height (cm)").scale(0.26)
        axis_title.move_to([(self.hist_x_left + hist_x_right) / 2, self.hist_baseline_y - 0.53, 0])

        pop_x = self.hist_x_left + (pop_mean - self.hist_min) * self.ppc
        pop_line = Line([pop_x, self.hist_baseline_y, 0], [pop_x, self.hist_baseline_y + 2.30, 0], color=GREEN)
        pop_mean_label = Text(f"Pop mean = {pop_mean:.1f} cm", color=GREEN).scale(0.24)
        pop_mean_label.move_to([pop_x, self.hist_baseline_y + 2.50, 0])

        self.play(
            FadeIn(x_axis), FadeIn(bin_lines), FadeIn(ticks), FadeIn(tick_lbl), FadeIn(axis_title),
            FadeIn(pop_line), FadeIn(pop_mean_label),
        )

        sample_title = Text("Sample 1  (with replacement)").scale(0.34)
        sample_title.move_to(RIGHT * 4.35 + UP * 3.05)
        slot_x = 3.85
        sample_targets = [
            slot_x * RIGHT + 2.10 * UP,
            slot_x * RIGHT + 1.20 * UP,
            slot_x * RIGHT + 0.30 * UP,
            slot_x * RIGHT + 0.60 * DOWN,
            slot_x * RIGHT + 1.50 * DOWN,
        ]

        for i in range(1, 9):
            self.show_sample_round(rng, i, population_records, sample_targets, sample_title)

        speed_text = Text("Sampling more ...").scale(0.36)
        speed_text.move_to(RIGHT * 4.0 + UP * 0.6)
        self.play(FadeIn(speed_text), FadeOut(sample_title))
        for _ in range(30):
            self.show_fast_round(rng, population_records)
        self.play(FadeOut(speed_text))

        self.wait(2.0)


class GroupDifferenceSampling(Scene):
    """Sex-colored sampling and distribution of male-female mean differences."""

    def _make_dot(self, diff_val: float) -> Dot:
        raw = int((diff_val - self.hist_min) / self.bin_width_cm)
        bin_idx = max(0, min(raw, self.n_bins - 1))
        count = self.bin_counts.get(bin_idx, 0)
        bx = self.hist_x_left + (bin_idx + 0.5) * self.bin_width_cm * self.ppc
        by = self.hist_baseline_y + self.dot_r + count * (2 * self.dot_r + 0.018)
        self.bin_counts[bin_idx] = count + 1
        self.total_dots += 1
        return Dot(point=[bx, by, 0], radius=self.dot_r, color=ORANGE)

    def _update_pct_labels(self, animate: bool = True) -> None:
        if self.total_dots == 0:
            return

        anims = []
        for bin_idx, count in self.bin_counts.items():
            pct = count / self.total_dots * 100
            bx = self.hist_x_left + (bin_idx + 0.5) * self.bin_width_cm * self.ppc
            by = self.hist_baseline_y + count * (2 * self.dot_r + 0.018) + self.dot_r + 0.12
            new_lbl = Text(f"{pct:.0f}%", color=ORANGE).scale(0.20)
            new_lbl.move_to([bx, by, 0])
            old = self.pct_labels.get(bin_idx)
            if old is None:
                self.pct_labels[bin_idx] = new_lbl
                if animate:
                    anims.append(FadeIn(new_lbl))
                else:
                    self.add(new_lbl)
            else:
                if animate:
                    anims.append(Transform(old, new_lbl))
                else:
                    old.become(new_lbl)

        if animate and anims:
            self.play(*anims, run_time=0.20)

    def show_group_round(
        self,
        rng: random.Random,
        round_number: int,
        population_records: list[PersonRecord],
        sample_targets: list,
        sample_title: Text,
    ) -> None:
        sampled = rng.choices(population_records, k=5)
        for _ in range(20):
            sample_m = [r for r in sampled if r.sex == "M"]
            sample_f = [r for r in sampled if r.sex == "F"]
            if sample_m and sample_f:
                break
            sampled = rng.choices(population_records, k=5)
        else:
            sample_m = [sampled[0]]
            sample_f = [sampled[1]]

        new_title = Text(f"Simple random sample {round_number}  (n=5)").scale(0.34)
        new_title.move_to(sample_title)
        if round_number == 1:
            self.play(FadeIn(sample_title))
        else:
            self.play(Transform(sample_title, new_title))

        sample_box = VGroup()
        for slot, rec in enumerate(sampled):
            src = self.person_glyphs[rec.pid - 1]
            cp = src.copy().scale(0.54).move_to(sample_targets[slot])
            self.play(Indicate(src, color=GREEN, scale_factor=1.08), run_time=0.18)
            self.play(TransformFromCopy(src, cp), run_time=0.25)
            sample_box.add(cp)

        mean_m = sum(r.height_cm for r in sample_m) / len(sample_m)
        mean_f = sum(r.height_cm for r in sample_f) / len(sample_f)
        diff = mean_f - mean_m

        m_expr = " + ".join(str(r.height_cm) for r in sample_m)
        f_expr = " + ".join(str(r.height_cm) for r in sample_f)
        fm = MathTex(r"\bar{X}_{M} = (" + m_expr + r")/" + str(len(sample_m)) + r" = " + f"{mean_m:.1f}", color=BLUE).scale(0.36)
        ff = MathTex(r"\bar{X}_{F} = (" + f_expr + r")/" + str(len(sample_f)) + r" = " + f"{mean_f:.1f}", color=RED).scale(0.36)
        fd = MathTex(r"D = \bar{X}_{F} - \bar{X}_{M} = " + f"{diff:.1f}", color=ORANGE).scale(0.42)
        # Place calculations above the histogram.
        fm.move_to(RIGHT * 5.2 + UP * 1.20)
        ff.next_to(fm, DOWN, buff=0.18)
        fd.next_to(ff, DOWN, buff=0.22)

        self.play(Write(fm), Write(ff), run_time=0.85)
        self.play(Write(fd), run_time=0.45)

        dot = self._make_dot(diff)
        self.play(TransformFromCopy(fd, dot), run_time=0.45)
        self._update_pct_labels(animate=True)

        self.play(FadeOut(sample_box), FadeOut(fm), FadeOut(ff), FadeOut(fd), run_time=0.36)

    def show_fast_round(self, rng: random.Random, population_records: list[PersonRecord]) -> None:
        sampled = rng.choices(population_records, k=5)
        for _ in range(20):
            sample_m = [r for r in sampled if r.sex == "M"]
            sample_f = [r for r in sampled if r.sex == "F"]
            if sample_m and sample_f:
                break
            sampled = rng.choices(population_records, k=5)
        else:
            sample_m = [sampled[0]]
            sample_f = [sampled[1]]

        mean_m = sum(r.height_cm for r in sample_m) / len(sample_m)
        mean_f = sum(r.height_cm for r in sample_f) / len(sample_f)
        diff = mean_f - mean_m
        dot = self._make_dot(diff)
        self.play(GrowFromPoint(dot, [dot.get_x(), self.hist_baseline_y, 0]), run_time=0.10)
        self._update_pct_labels(animate=False)

    def construct(self) -> None:
        rng = random.Random(2031)

        self.hist_baseline_y = -3.10
        self.hist_x_left = -5.80
        self.bin_width_cm = 2.0
        self.dot_r = 0.060
        self.bin_counts: dict[int, int] = {}
        self.total_dots = 0
        self.pct_labels: dict[int, Text] = {}

        males = [
            PersonRecord(pid=i + 1, height_cm=rng.randint(168, 195), sex="M")
            for i in range(8)
        ]
        females = [
            PersonRecord(pid=8 + i + 1, height_cm=rng.randint(155, 182), sex="F")
            for i in range(8)
        ]
        population_records = males + females

        pop_diff = sum(r.height_cm for r in females) / len(females) - sum(r.height_cm for r in males) / len(males)

        # Center histogram around population difference.
        half_range = 20.0
        self.hist_min = pop_diff - half_range
        self.hist_max = pop_diff + half_range
        self.ppc = 11.6 / (self.hist_max - self.hist_min)
        self.n_bins = int((self.hist_max - self.hist_min) / self.bin_width_cm)

        self.person_glyphs = VGroup(
            *[PersonGlyph(rec, outer_scale=0.92, color_by_sex=True) for rec in population_records]
        )
        self.person_glyphs.arrange_in_grid(rows=4, cols=4, buff=(0.28, 0.22))
        self.person_glyphs.move_to(LEFT * 3.4 + UP * 1.35)

        sex_legend = VGroup(
            Text("Male", color=BLUE).scale(0.26),
            Text("Female", color=RED).scale(0.26),
        ).arrange(RIGHT, buff=0.35)
        sex_legend.move_to(LEFT * 3.4 + UP * 3.2)

        self.play(FadeIn(self.person_glyphs, lag_ratio=0.04, run_time=1.8), FadeIn(sex_legend))

        hist_x_right = self.hist_x_left + (self.hist_max - self.hist_min) * self.ppc
        x_axis = Line([self.hist_x_left, self.hist_baseline_y, 0], [hist_x_right, self.hist_baseline_y, 0])
        bin_lines = VGroup(
            *[
                DashedLine(
                    [self.hist_x_left + b * self.bin_width_cm * self.ppc, self.hist_baseline_y, 0],
                    [self.hist_x_left + b * self.bin_width_cm * self.ppc, self.hist_baseline_y + 2.30, 0],
                    dash_length=0.07,
                    dashed_ratio=0.40,
                    stroke_width=0.9,
                )
                for b in range(self.n_bins + 1)
            ]
        )
        ticks = VGroup()
        tick_lbl = VGroup()
        tick_start = int(self.hist_min // 5) * 5
        tick_end = int(self.hist_max // 5) * 5
        for val in range(tick_start, tick_end + 1, 5):
            tx = self.hist_x_left + (val - self.hist_min) * self.ppc
            ticks.add(Line([tx, self.hist_baseline_y - 0.09, 0], [tx, self.hist_baseline_y + 0.09, 0]))
            lbl = Text(str(val)).scale(0.20)
            lbl.move_to([tx, self.hist_baseline_y - 0.28, 0])
            tick_lbl.add(lbl)
        axis_title = Text("Difference in means  (Female - Male)").scale(0.26)
        axis_title.move_to([(self.hist_x_left + hist_x_right) / 2, self.hist_baseline_y - 0.53, 0])

        pop_ref_x = self.hist_x_left + (pop_diff - self.hist_min) * self.ppc
        pop_ref_line = Line([pop_ref_x, self.hist_baseline_y, 0], [pop_ref_x, self.hist_baseline_y + 2.30, 0], color=GREEN)
        pop_ref_label = Text(f"Pop diff = {pop_diff:.1f}", color=GREEN).scale(0.24)
        pop_ref_label.move_to([pop_ref_x, self.hist_baseline_y + 2.50, 0])

        self.play(
            FadeIn(x_axis), FadeIn(bin_lines), FadeIn(ticks), FadeIn(tick_lbl), FadeIn(axis_title),
            FadeIn(pop_ref_line), FadeIn(pop_ref_label),
        )

        sample_title = Text("Simple random sample 1  (n=5)").scale(0.34)
        sample_title.move_to(RIGHT * 4.35 + UP * 3.05)
        sample_targets = [
            RIGHT * 2.9 + UP * 2.15,
            RIGHT * 2.9 + UP * 1.35,
            RIGHT * 2.9 + UP * 0.55,
            RIGHT * 2.9 + DOWN * 0.25,
            RIGHT * 2.9 + DOWN * 1.05,
        ]

        for i in range(1, 9):
            self.show_group_round(rng, i, population_records, sample_targets, sample_title)

        speed_text = Text("Sampling more ...").scale(0.36)
        speed_text.move_to(RIGHT * 4.1 + DOWN * 0.2)
        self.play(FadeIn(speed_text), FadeOut(sample_title))
        for _ in range(30):
            self.show_fast_round(rng, population_records)
        self.play(FadeOut(speed_text))

        self.wait(2.0)
