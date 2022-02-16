'''
Use build.bat to build and upload to PyPi.
Always make sure the version number is correct before building!
'''
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setuptools.setup(
	name = "rot2prog",
	version = "0.0.5",
	author = "TJ Scherer",
	author_email = "tjtractorboy@gmail.com",
	description = "A python interface to the Alfa ROT2Prog Controller.",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	url = "https://github.com/tj-scherer/rot2prog",
	project_urls = {
		"Bug Tracker": "https://github.com/tj-scherer/rot2prog/issues",
	},
	classifiers = [
		"Programming Language :: Python :: 3.10",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Topic :: Scientific/Engineering :: Astronomy",
	],
	package_dir = {"": "src"},
	packages = setuptools.find_packages(where = "src"),
	install_requires = [
		'pyserial',
	],
	python_requires = ">=3.10",
)