^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package sick_safetyscanners2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------
* Added launch file exposing the driver settings as launch arguments and
  supporting composition
* Added support for running the driver as a composable node, publishing scans
  as unique_ptr for intra process communication
* Added min_range and max_range parameters and report readings below the
  minimum range as -infinity according to REP 117
* Fixed laser scan timestamp to refer to the first ray instead of the time the
  completed scan was received
* Added Docker environment for ROS 2 Jazzy
* Contributors: sgsuh

1.0.5 (2026-05-07)
------------------
* Updated maintainer list in package.xml
* Added error_info_codes from status_overview service to documentation
* Added status_overview service to return additional device status information
* Contributors: Christian Eichmann

1.0.4 (2024-09-24)
------------------
* possible fix for out of range
* Add material for correct representation in Gazebo Sim.
* Enable workin in Gazebo under humble.
* enabled gazebo integration in urdf
* generated description folder using RTW
* diagnostics for lifecycle node aswell
* refactor: combine Node and LifeCycle node implementations
* Contributors: Dr. Denis Štogl, Lennart Puck, Nibanovic, Rein Appeldoorn

1.0.3 (2021-12-22)
------------------
* Fixes unsafe pointer access in UDP callback
* Implement lifecycle node 
* Added functionality to allow multicast
* set not using the default sick angles as default
* moved changeSensor settings to be always be invoked
* fixed typo in launch file
* Contributors: Brice, Erwin Lejeune, Soma Gallai, Lennart Puck, Tanmay

1.0.2 (2021-03-15)
------------------
* added missing dependencies to package xml
* Contributors: Lennart Puck

1.0.1 (2021-03-05)
------------------
* changed the parameter callback interface so its only triggered
  when the parameters of this node are called
* Contributors: Lennart Puck

1.0.0 (2021-01-11)
------------------

* Initial Release
