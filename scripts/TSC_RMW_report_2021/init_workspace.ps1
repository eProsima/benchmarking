# Copyright 2021 Proyectos y Sistemas de Mantenimiento SL (eProsima).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

Param (
[string]$WS_DIR = "./rmw_report_ws",
[switch]$help
)

function print_usage
{
    Write-Output "------------------------------------------------------------------------"
    Write-Output "Scritp to init the workspace for RMW report 2021."
    Write-Output "------------------------------------------------------------------------"
    Write-Output "OPTIONAL ARGUMENTS:"
    Write-Output "   -h                 Print help"
    Write-Output "   -d [directory]     The directory where the workspace should be created"
    Write-Output "                      [Defaults: ./rmw_report_ws]"
    Write-Output ""
    Write-Output "EXAMPLE: bash init_workspace -d temp/report_ws"
    Exit
}

#Processing input arguments

if ($help)
{
    print_usage
}

if (!(Test-Path $WS_DIR))
{
    New-Item $WS_DIR -ItemType Directory
}

# Installing ROS dependencies

choco install -y python --version 3.8.3
choco install -y vcredist2013 vcredis140
choco install -y cmake

#curl https://github.com/ros2/choco-packages/archive/2020-02-24.zip -o choco_2020-02-24.zip
#Expand-Archive -Path choco_2020-02-24.zip -Force

choco install -y -s .\choco-packages-2020-02-24 asio
choco install -y -s .\choco-packages-2020-02-24 cunit
choco install -y -s .\choco-packages-2020-02-24 eigen
choco install -y -s .\choco-packages-2020-02-24 tinyxml-usestl
choco install -y -s .\choco-packages-2020-02-24 tinyxml2
choco install -y -s .\choco-packages-2020-02-24 log4cxx
choco install -y -s .\choco-packages-2020-02-24 bullet

choco install -y cppcheck curl git winflexbison3
 
pip install -U colcon-common-extensions coverage flake8 flake8-blind-except flake8-builtins flake8-class-newline flake8-comprehensions flake8-deprecated flake8-docstrings flake8-import-order flake8-quotes mock mypy==0.761 pep8 pydocstyle pytest pytest-mock vcstool

# Moving to the WS

$RUN_DIR = Get-Location
cd $WS_DIR

# Downloading ROS2
if (!(Test-Path src))
{
    New-Item src -ItemType Directory
}

curl https://raw.githubusercontent.com/osrf/TSC-RMW-Reports/main/humble/ros2.repos -o ros2.repos

vcs import --input ros2.repos src

cd src
git clone https://gitlab.com/ApexAI/performance_test.git
cd performance_test
git remote add company https://gitlab.com/MiguelCompany/performance_test
git fetch company
git checkout c230727  # HEAD of company/feature/build-on-windows
cd ../../

# Compiling ROS2
colcon build --packages-up-to performance_test ros2cli_common_extensions --merge-install --cmake-args -DBUILD_TESTING=OFF --no-warn-unused-cli -DCMAKE_BUILD_TYPE=Release -DINSTALL_EXAMPLES=OFF -DSECURITY=ON -DCOMPILE_EXAMPLES=OFF

# Returning to original directory and exit

cd $RUN_DIR

