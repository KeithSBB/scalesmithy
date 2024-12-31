from setuptools import setup, find_packages

setup(
        name='scalesmithy',
        version='0.1.0',
       # packages=[''],  #         packages=find_packages('.'),
        url='https://github.com/KeithSBB/Scale_Smithy',
        license='TBD',
        author='KeithSBB',
        author_email='keith@santabayanian.com',
        description='Musical scales Tool',
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Musicians",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.11"],
        keywords="music, music theory, scales, chords, composition",
        python_requires=">=3.11, <4",
        install_requires=['pyQt6', 'mido']
)


