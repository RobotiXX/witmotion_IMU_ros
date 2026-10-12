"""Regression: ROS/Qt exits cleanly on signals, without attached hardware.

Source the built workspace, then run python3 -m unittest discover -s test.
"""
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest

from ament_index_python.packages import get_package_prefix


class ShutdownTest(unittest.TestCase):
    def test_shutdown_signals(self):
        executable = Path(get_package_prefix('witmotion_ros')) / (
            'lib/witmotion_ros/witmotion_ros_node'
        )
        for sig in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(signal=sig), tempfile.TemporaryFile(mode='w+') as log:
                process = subprocess.Popen([
                    str(executable), '--ros-args',
                    '-p', 'port:=musohu_shutdown_test_missing_port',
                    '-p', 'timeout_ms:=0',
                ], stdout=log, stderr=subprocess.STDOUT,
                    env={**os.environ, 'ROS_DOMAIN_ID': '89'})
                try:
                    deadline = time.monotonic() + 10
                    started = False
                    while process.poll() is None and time.monotonic() < deadline:
                        log.seek(0)
                        if 'Opening device' in log.read():
                            started = True
                            break
                        time.sleep(0.1)
                    self.assertTrue(started, 'Driver did not start')
                    process.send_signal(sig)
                    self.assertEqual(process.wait(timeout=10), 0)
                    log.seek(0)
                    self.assertNotIn('deadlock', log.read())
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()


if __name__ == '__main__':
    unittest.main()
