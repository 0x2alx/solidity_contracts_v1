import brownie, pytest, pathlib, json, random


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_gas_optimization(temp_tests, a):
    ctr = temp_tests.deploy({"from": a[0]})
    for i in range(0, 10):
        bbb = ctr.fill_arr()
        # print(bbb.return_value)
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$4")
    for i in range(0, 10):
        bbb2 = ctr.fill_arr2()
        # print(bbb2.return_value)
    assert False
