from algorithm import compute_map, parse_date, parse_time, print_time

import pytest


TESTS = {
    "ZUE_1": {
        "destination": "Zürich HB",
        "date": "2023-09-16",
        "time": "15:43",
        "time_lb": "14:00",
        "expected_results": {
            "Bülach, Mettmenriet": "15:04",
            "Bachenbülach, alte Post": "15:07",
            "Höri, Gemeindehaus": "14:46",
            "Neerach, Post": "14:58",
            "Uster, Pfannenstielstrasse": "15:05",
            "Stadel b. N., Zentrum": "14:56",
            "Winkel, Zentrum": "14:50",
            "Thalwil, Ebnet": "15:10",
            "Wädenswil, Hangenmoos": "15:08",
            "Wädenswil, Sandhof": "15:07",
        }
    }
}

@pytest.fixture(scope='session')
def zue_1_result():
    testcase = TESTS["ZUE_1"]
    mapping = compute_map(
        testcase["destination"], 
        parse_date(testcase["date"]), 
        parse_time(testcase["time"]),
        earliest_departure=parse_time(testcase["time_lb"])
    )
    return mapping


@pytest.mark.parametrize("location", TESTS["ZUE_1"]["expected_results"].keys())
def test_zue_1(location, zue_1_result):
    for startpoint in zue_1_result.values():
        name = startpoint["name"]
        if name == location:
            expected_departure = parse_time(TESTS["ZUE_1"]["expected_results"][location])
            departure = startpoint["departure"]
            assert departure == expected_departure, f"{print_time(departure)} = {print_time(expected_departure)}"

