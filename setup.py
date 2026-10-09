import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'survivor_sim'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'),
         glob('urdf/*.urdf')),
        (os.path.join('share', package_name, 'worlds'),
         glob('worlds/*.sdf')),
        (os.path.join('share', package_name, 'meshes'),
         glob('meshes/*.stl')),
        *[(os.path.join('share', package_name, folder),
            [os.path.join(folder, filename) for filename in files])
        for folder, _, files in os.walk('models')
        if files
        ],
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sreerag',
    maintainer_email='sreerag0607@gmail.com',
    description='Mine rescue robot simulation using Gazebo Classic',
    license='MIT',
    entry_points={
        'console_scripts': [
        ],
    },
)
