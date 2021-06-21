import setuptools

BASE_REQUIREMENTS = [
 'easyrpc>=0.241',
 'aiopyql>=0.359',
 'gunicorn',
 'python-multipart',
]

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='easycaching',  
     version='NEXTVERSION',
     packages=setuptools.find_packages(include=['easycaching'], exclude=['build']),
     author="Joshua Jamison",
     author_email="joshjamison1@gmail.com",
     description="Shared, persistent, and smart caching via a single shared interface for storing and retreiving data from memory among many processes(forks) of an application",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/codemation/easycaching",
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     python_requires='>=3.7, <4',   
     install_requires=BASE_REQUIREMENTS,
     extras_require={}
 )