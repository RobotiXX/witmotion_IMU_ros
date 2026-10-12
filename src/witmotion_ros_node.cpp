#include "witmotion_ros.h"

#include <QMetaObject>
#include <thread>

int main(int argc, char *argv[]) {

  QCoreApplication app(argc, argv);
  rclcpp::InitOptions options{};
  options.shutdown_on_signal = true;
  rclcpp::init(argc, argv, options);
  ROSWitmotionSensorController &controller = ROSWitmotionSensorController::Instance();
  auto node = controller.Start();
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);

  // This callback runs inside Context::shutdown(). Calling shutdown again
  // deadlocks the context. Queue Qt's exit on its own thread instead.
  rclcpp::on_shutdown([&executor, &app]() {
    executor.cancel();
    QMetaObject::invokeMethod(&app, "quit", Qt::QueuedConnection);
  });

  std::thread spinThread([&executor]() { executor.spin(); });

  RCLCPP_INFO(rclcpp::get_logger("MinimalPublisher"), "QT spin !!!!!");
  int result = app.exec();

  executor.cancel();
  if (rclcpp::ok()) {
    rclcpp::shutdown();
  }
  // Keep executor and node alive until the ROS thread has stopped.
  spinThread.join();
  executor.remove_node(node);
  controller.Stop();
  node.reset();
  return result;
}
