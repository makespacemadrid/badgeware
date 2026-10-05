from tshirt_templates.layout import compute_panels, expand_badges, page_size_points, place_badges


def test_page_size_points_applies_orientation():
    assert page_size_points() == (595.28, 841.89)
    assert page_size_points("letter", "portrait") == (612.0, 792.0)
    assert page_size_points("letter", "landscape") == (792.0, 612.0)


def test_expand_badges_clamps_to_at_least_one_copy():
    assert expand_badges(["a", "b"], 0) == ["a", "b"]


def test_front_and_back_panels_are_side_by_side():
    panels = compute_panels(612, 792, ["front", "back"])
    assert set(panels) == {"front", "back"}
    assert panels["front"][0] < panels["back"][0]
    assert panels["front"][2] == panels["back"][2]


def test_grid_layout_places_each_copy_on_each_selected_panel():
    page_size, layouts = place_badges(
        badge_ids=["alpha", "beta"],
        sides=["front", "back"],
        mode="grid",
        copies=2,
    )
    assert page_size == (595.28, 841.89)
    assert len(layouts) == 2
    assert all(len(layout.placements) == 4 for layout in layouts)


def test_separate_side_layouts_paginate_badges_at_requested_size_and_spacing():
    badge_ids = [f"badge-{index}" for index in range(80)]

    _, layouts = place_badges(
        badge_ids,
        ["front"],
        mode="grid",
        badge_size_inches=1.5,
        spacing_inches=0.25,
        separate_side_pages=True,
    )

    assert len(layouts) > 1
    assert sum(len(layout.placements) for layout in layouts) == len(badge_ids)
    assert all(layout.side == "front" for layout in layouts)
    for layout in layouts:
        for placement in layout.placements:
            assert layout.x <= placement.x <= layout.x + layout.width - placement.width
            assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_combined_front_back_layout_keeps_single_panel_per_side_for_compatibility():
    badge_ids = [f"badge-{index}" for index in range(80)]

    _, layouts = place_badges(badge_ids, ["front", "back"], separate_side_pages=False)

    assert [layout.side for layout in layouts] == ["front", "back"]




def test_custom_page_margin_and_panel_gap_change_panel_geometry():
    _, default_layouts = place_badges(["alpha"], ["front", "back"])
    _, custom_layouts = place_badges(
        ["alpha"],
        ["front", "back"],
        page_margin_inches=1.0,
        panel_gap_inches=1.0,
    )

    assert custom_layouts[0].x > default_layouts[0].x
    assert custom_layouts[0].width < default_layouts[0].width
    assert custom_layouts[1].x - (custom_layouts[0].x + custom_layouts[0].width) == 72.0

def test_grid_layout_shrinks_spacing_to_keep_dense_badges_in_bounds():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(20)],
        ["front", "back"],
        mode="grid",
        badge_size_inches=1.0,
        spacing_inches=0.5,
    )

    assert len(layouts) == 2
    for layout in layouts:
        assert len(layout.placements) == 20
        for placement in layout.placements:
            assert layout.x <= placement.x <= layout.x + layout.width - placement.width
            assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_rows_layout_shrinks_spacing_to_keep_dense_badges_in_bounds():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(20)],
        ["front", "back"],
        mode="rows",
        badge_size_inches=1.0,
        spacing_inches=0.5,
    )

    for layout in layouts:
        for placement in layout.placements:
            assert layout.x <= placement.x <= layout.x + layout.width - placement.width
            assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_landscape_layout_uses_wide_page_size():
    page_size, layouts = place_badges(
        badge_ids=["alpha"],
        sides=["front"],
        page_size="a4",
        orientation="landscape",
    )

    assert page_size == (841.89, 595.28)
    assert layouts[0].width > layouts[0].height


def test_scatter_layout_is_deterministic():
    first = place_badges(["a", "b", "c"], ["front"], mode="scatter")[1][0].placements
    second = place_badges(["a", "b", "c"], ["front"], mode="scatter")[1][0].placements
    assert first == second


def test_decorative_layout_modes_place_badges_in_bounds():
    for mode in ["circle", "spiral", "wave"]:
        _, layouts = place_badges(
            [f"badge-{index}" for index in range(8)],
            ["front"],
            mode=mode,
            badge_size_inches=1.0,
            spacing_inches=0.1,
        )
        layout = layouts[0]

        assert len(layout.placements) == 8
        assert any(placement.rotation != 0 for placement in layout.placements)
        for placement in layout.placements:
            assert layout.x <= placement.x <= layout.x + layout.width - placement.width
            assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_single_badge_decorative_layout_modes_center_badge():
    for mode in ["circle", "spiral", "wave"]:
        _, layouts = place_badges(["alpha"], ["front"], mode=mode)
        layout = layouts[0]
        placement = layout.placements[0]

        assert placement.x == layout.x + (layout.width - placement.width) / 2
        assert placement.y == layout.y + (layout.height - placement.height) / 2


def test_border_layout_places_badges_around_panel_edges():
    _, layouts = place_badges(["a", "b", "c", "d"], ["front"], mode="border")
    layout = layouts[0]
    xs = [placement.x for placement in layout.placements]
    ys = [placement.y for placement in layout.placements]

    assert len(layout.placements) == 4
    assert min(xs) >= layout.x
    assert max(xs) <= layout.x + layout.width
    assert min(ys) >= layout.y
    assert max(ys) <= layout.y + layout.height
    assert {placement.rotation for placement in layout.placements}.issubset({-90.0, 0.0, 90.0, 180.0})


def test_m_pixel_layout_places_badges_in_bounds_with_square_pixels():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(12)],
        ["front"],
        mode="m-pixels",
        badge_size_inches=1.0,
        spacing_inches=0.1,
    )

    layout = layouts[0]

    assert len(layout.placements) == 19
    assert {placement.rotation for placement in layout.placements} == {0.0}
    for placement in layout.placements:
        assert placement.width == placement.height
        assert layout.x <= placement.x <= layout.x + layout.width - placement.width
        assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_m_pixel_layout_repeats_selected_badges_to_fill_shape():
    _, layouts = place_badges(
        ["alpha", "beta"],
        ["front"],
        mode="m-pixels",
        badge_size_inches=1.0,
        spacing_inches=0.1,
    )

    placements = layouts[0].placements

    assert len(placements) == 13
    assert [placement.badge_id for placement in placements[:4]] == ["alpha", "beta", "alpha", "beta"]
    assert {placement.badge_id for placement in placements} == {"alpha", "beta"}


def test_crowded_m_pixel_layout_keeps_the_m_shape():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(14)],
        ["front"],
        mode="m-pixels",
        badge_size_inches=1.0,
        spacing_inches=0.1,
    )

    placements = layouts[0].placements
    distinct_rows = {round(placement.y, 3) for placement in placements}
    distinct_columns = {round(placement.x, 3) for placement in placements}

    assert len(placements) == 19
    assert len(distinct_rows) == 7
    assert len(distinct_columns) == 7
    assert all(placement.width <= 72.0 for placement in placements)
    assert [placement.badge_id for placement in placements[:14]] == [
        f"badge-{index}" for index in range(14)
    ]


def test_m_pixel_layout_scales_dense_patterns_to_stay_in_bounds():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(25)],
        ["front", "back"],
        mode="m-pixels",
        badge_size_inches=4.0,
        spacing_inches=0.0,
    )

    assert all(len(layout.placements) == 25 for layout in layouts)
    for layout in layouts:
        assert any(placement.width < 4.0 * 72 for placement in layout.placements)
        for placement in layout.placements:
            assert placement.width == placement.height
            assert layout.x <= placement.x <= layout.x + layout.width - placement.width
            assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_m_pixel_no_shrink_layout_uses_line_above_for_overflow():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(14)],
        ["front"],
        mode="m-pixels-no-shrink",
        badge_size_inches=1.0,
        spacing_inches=0.1,
    )

    placements = layouts[0].placements
    row_positions = sorted({round(placement.y, 3) for placement in placements})

    assert len(placements) == 14
    adjacent_gap = row_positions[1] - row_positions[0]
    overflow_gap = row_positions[-1] - row_positions[-2]

    assert len(row_positions) == 6
    assert overflow_gap > adjacent_gap * 1.5
    assert {placement.width for placement in placements} == {72.0}
    assert [placement.badge_id for placement in placements] == [
        f"badge-{index}" for index in range(14)
    ]


def test_m_pixel_no_shrink_layout_expands_to_square_fallbacks_without_shrinking():
    cases = [(23, 5, 7), (37, 9, 9), (69, 11, 10)]

    for count, expected_columns, expected_rows in cases:
        _, layouts = place_badges(
            [f"badge-{index}" for index in range(count)],
            ["front"],
            mode="m-pixels-no-shrink",
            badge_size_inches=0.6,
            spacing_inches=0.1,
        )
        placements = layouts[0].placements
        columns = {round(placement.x, 3) for placement in placements}
        rows = {round(placement.y, 3) for placement in placements}

        assert len(placements) == count
        assert len(columns) == expected_columns
        assert len(rows) == expected_rows
        assert {placement.width for placement in placements} == {0.6 * 72}


def test_layout_can_use_different_badges_per_side():
    _, layouts = place_badges(
        {"front": ["front-only"], "back": ["back-only", "shared"]},
        ["front", "back"],
        mode="grid",
    )

    placements_by_side = {
        layout.side: [placement.badge_id for placement in layout.placements]
        for layout in layouts
    }
    assert placements_by_side["front"] == ["front-only"]
    assert placements_by_side["back"] == ["back-only", "shared"]


def test_layout_can_size_each_side_to_a_separate_page():
    page_size, layouts = place_badges(
        {"front": ["front-only"], "back": ["back-only"]},
        ["front", "back"],
        separate_side_pages=True,
    )

    assert page_size == (595.28, 841.89)
    assert len(layouts) == 2
    assert layouts[0].x == layouts[1].x
    assert layouts[0].width == layouts[1].width
    assert layouts[0].width > page_size[0] / 2
