# cziPy for WSI.czi -> png patches.
### Using python-bioformats to tile/patch whole slide images in .czi format (for Zeiss WSI scanners)

## Basic usage
To run an experiment, while in the root directory of the project, the command:
```
python cziPy.py --czi_dir "/dir/of/czi/files/" --patch_dir "/dir/target/for/patches/"
```

To see all possible arguments, run the following:
```
python cziPy.py --help
```

## Environment setup (tested for ubuntu)
1. Download a copy of the repository
```
git clone https://github.com/CraigMyles/cziPy
```
2. cd into cziPy direcory
```
cd cziPy/
```
3. Create the environment
```
make create_environment
```
4. Install Java

```
make install_java
```
5. Activate cziPy environment

```
conda activate cziPy
```
