import unittest
from unittest.mock import Mock, patch

from modules.device_adapter import DeviceAdapter
from modules import taobao
from modules.utils import ManualVerificationRequired


def android_device(xml):
    adapter = DeviceAdapter.__new__(DeviceAdapter)
    adapter.device_type = "uiautomator2"
    adapter._device = Mock()
    adapter._device.dump_hierarchy.return_value = xml
    return adapter


class TaskStatusTests(unittest.TestCase):
    def test_android_verification_overlay_stops_task(self):
        # Text observed in the captured Android verification overlay.
        device = android_device(
            '<hierarchy><node text="验证码拦截"/>'
            '<node text="亲，请拖动下方滑块完成验证"/></hierarchy>'
        )
        with self.assertRaises(ManualVerificationRequired):
            taobao.do_time_5_task(device)

    def test_verification_during_countdown_stops_task(self):
        device = android_device('<hierarchy><node text="浏览5秒"/></hierarchy>')
        device._device.dump_hierarchy.side_effect = [
            '<hierarchy><node text="浏览5秒"/></hierarchy>',
            '<hierarchy><node text="向右滑动验证"/></hierarchy>',
        ]
        with patch.object(taobao.time, "sleep"):
            with self.assertRaises(ManualVerificationRequired):
                taobao.do_time_5_task(device)

    def test_task_list_description_is_not_a_task_page(self):
        device = Mock()
        device.dump_hierarchy.return_value = {"text": "累计任务奖励 浏览5秒"}
        with patch.object(taobao.time, "monotonic", side_effect=[0, 0, 16]), \
             patch.object(taobao.time, "sleep"):
            self.assertFalse(taobao.do_time_5_task(device))

    def test_completed_task_does_not_wait_again(self):
        device = Mock()
        device.dump_hierarchy.return_value = {"text": "任务已完成"}
        with patch.object(taobao.time, "sleep") as sleep:
            self.assertTrue(taobao.do_time_5_task(device))
            sleep.assert_not_called()

    def test_recognized_browsing_page_waits(self):
        device = Mock()
        device.dump_hierarchy.return_value = {"text": "浏览5秒"}
        with patch.object(taobao.time, "sleep") as sleep:
            self.assertTrue(taobao.do_time_5_task(device))
            sleep.assert_called_once_with(8)

    def test_failed_task_stops_instead_of_repeating(self):
        device = Mock()
        with patch("builtins.input", return_value="1"), \
             patch.object(taobao.time, "sleep"), \
             patch.object(taobao, "open_taobao_search"), \
             patch.object(taobao, "find_timeout_re", return_value=["去赚能量"]), \
             patch.object(taobao, "get_coin", return_value=30), \
             patch.object(taobao, "find_time_15_task", return_value=False), \
             patch.object(taobao, "find_time_5_task", return_value=True) as find_task, \
             patch.object(taobao, "do_time_5_task", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "未计入完成数"):
                taobao.run(device)
            self.assertEqual(find_task.call_count, 1)


if __name__ == "__main__":
    unittest.main()
