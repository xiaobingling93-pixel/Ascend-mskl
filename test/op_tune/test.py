import unittest
from unittest.mock import patch, MagicMock

from mskl.optune.tuner import AutotuneV2Scheduler


class TestAutotuneV2Scheduler(unittest.TestCase):
    def setUp(self):
        # 模拟基础依赖
        self.mock_configs = [{'param': 1}, {'param': 2}]
        self.mock_launch_params = {'device': 'cpu'}
        self.mock_manager = MagicMock()
        self.mock_manager.Queue.side_effect = [MagicMock(), MagicMock()]
        
        # 使用patch接管所有外部依赖
        self.patchers = [
            patch('multiprocessing.Manager', return_value=self.mock_manager),
            patch('multiprocessing.Pool'),
            patch('threading.Thread'),
            patch('os.sched_getaffinity'),
            patch('os.cpu_count'),
            patch('logging.getLogger')
        ]
        for patcher in self.patchers:
            patcher.start()
        
        # 初始化被测试对象
        self.scheduler = AutotuneV2Scheduler(
            configs=self.mock_configs,
            warmup_times=3,
            launch_params=self.mock_launch_params
        )
        
        # 注入模拟的AutotunerV2
        self.mock_autotuner = MagicMock()
        self.scheduler._auto_tuner = self.mock_autotuner

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_init(self):
        """测试对象初始化逻辑"""
        self.assertEqual(self.scheduler.task_num, 2)
        self.mock_manager.Queue.assert_called()
        self.mock_manager.Queue.assert_any_call()
        self.assertTrue(hasattr(self.scheduler, 'task_queue'))
        self.assertTrue(hasattr(self.scheduler, 'logging_queue'))

    def test_get_process_num_normal(self):
        """测试正常获取进程数逻辑"""
        with patch('os.sched_getaffinity', return_value=set(range(16))):
            result = AutotuneV2Scheduler._get_process_num()
            self.assertEqual(result, 8)  # 16/2=8

    def test_get_process_num_fallback(self):
        """测试CPU核心数获取失败的回退逻辑"""
        with patch('os.sched_getaffinity', side_effect=Exception('mock error')):
            with patch('os.cpu_count', return_value=64):
                result = AutotuneV2Scheduler._get_process_num()
                self.assertEqual(result, 32)  # min(64/2,32)

    def test_execute_full_flow(self):
        """测试完整执行流程"""
        # 配置模拟对象
        mock_compile_pool = MagicMock()
        mock_compile_task = MagicMock()
        mock_compile_pool.apply_async.return_value = mock_compile_task
        self.scheduler._compile_processes = 2
        
        # 执行主流程
        self.scheduler.execute()
        
        # 验证线程池创建
        self.mock_pool.assert_called_with(min(2, 2))
        
        # 验证任务提交
        self.assertEqual(mock_compile_pool.apply_async.call_count, 2)
        
        # 验证线程启动
        self.mock_thread.assert_any_call(target=self.scheduler._log_listener)
        self.mock_thread.assert_any_call(target=self.scheduler._launch_task)

    def test_compile_task_success(self):
        """测试编译任务成功场景"""
        self.mock_autotuner.gen_src_file.return_value = 'mock_src'
        self.mock_autotuner.compile.return_value = 'mock_bin'
        
        self.scheduler._compile_task(0)
        
        self.mock_autotuner.gen_src_file.assert_called_with(0)
        self.mock_autotuner.compile.assert_called_with('mock_src')
        self.scheduler.task_queue.put.assert_called_with((0, 'mock_bin'))
        self.mock_autotuner.clean_temp_files.assert_called()

    def test_compile_task_failure(self):
        """测试编译任务失败场景"""
        self.mock_autotuner.gen_src_file.side_effect = Exception('mock error')
        
        self.scheduler._compile_task(1)
        
        self.scheduler.task_queue.put.assert_called_with((1, None))
        self.mock_autotuner.clean_temp_files.assert_called()

    def test_launch_task_normal(self):
        """测试启动任务正常流程"""
        self.scheduler.task_queue.get = MagicMock(side_effect=[
            (0, 'mock_bin'), (1, 'mock_bin2'), (None, None)
        ])
        self.mock_autotuner.launch.return_value = 0.5
        
        self.scheduler._launch_task()
        
        self.assertEqual(self.mock_autotuner.launch.call_count, 2)
        self.scheduler.logging_queue.put.assert_any_call((0, 0.5))
        self.scheduler.logging_queue.put.assert_any_call((1, 0.5))

    def test_log_listener(self):
        """测试日志监听器"""
        self.scheduler.logging_queue.get = MagicMock(side_effect=[
            (0, 0.5), (1, 0.8), (None, None)
        ])
        
        self.scheduler._log_listener()
        
        self.mock_autotuner.show_result.assert_called_with({0:0.5, 1:0.8})
        self.mock_autotuner.save_result.assert_called_with({0:0.5, 1:0.8})
        self.mock_autotuner.remove_temp_dir.assert_called()

if __name__ == '__main__':
    unittest.main()