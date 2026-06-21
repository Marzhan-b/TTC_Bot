"""
Тесты для monitor/checker.py

Запуск: pytest tests/test_checker.py -v
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor.checker import parse_ping_time


def test_parse_ping_time_linux_success():
    """Проверяет, что время корректно извлекается из стандартного вывода Linux ping"""
    output = (
        "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n"
        "64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=12.3 ms\n"
        "\n"
        "--- 8.8.8.8 ping statistics ---\n"
        "3 packets transmitted, 3 received, 0% packet loss, time 2003ms\n"
        "rtt min/avg/max/mdev = 11.345/15.678/20.123/2.456 ms\n"
    )
    result = parse_ping_time(output, "linux")
    assert result == "15.678 ms"


def test_parse_ping_time_linux_no_match():
    """Если в выводе нет нужной строки — должна вернуться 'N/A'"""
    output = "some random text without rtt info"
    result = parse_ping_time(output, "linux")
    assert result == "N/A"

def test_parse_ping_time_windows_success():
    """Проверяет извлечение времени из вывода Windows ping"""
    output = (
        "Pinging 8.8.8.8 with 32 bytes of data:\n"
        "Reply from 8.8.8.8: bytes=32 time=14ms TTL=117\n"
        "\n"
        "Ping statistics for 8.8.8.8:\n"
        "    Packets: Sent = 3, Received = 3, Lost = 0 (0% loss),\n"
        "Approximate round trip times in milli-seconds:\n"
        "    Minimum = 12ms, Maximum = 16ms, Average = 14ms\n"
    )
    result = parse_ping_time(output, "windows")
    assert result == "14ms"


def test_parse_ping_time_empty_output():
    """Пустой вывод не должен вызывать ошибку, должен вернуть 'N/A'"""
    result = parse_ping_time("", "linux")
    assert result == "N/A"



def test_ping_host_returns_dict_with_correct_keys():
    """Проверяет, что ping_host всегда возвращает словарь с нужными ключами,
    независимо от того, доступен хост или нет"""
    from monitor.checker import ping_host
    result = ping_host("8.8.8.8")

    assert "host" in result
    assert "alive" in result
    assert "avg_time" in result
    assert "output" in result
    assert isinstance(result["alive"], bool)


def test_ping_host_unreachable_address():
    """Проверяет, что заведомо недоступный адрес возвращает alive=False
    без падения программы с ошибкой"""
    from monitor.checker import ping_host

    result = ping_host("192.0.2.1")

    assert result["alive"] == False
    assert result["host"] == "192.0.2.1"