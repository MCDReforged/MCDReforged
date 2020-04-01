set name=MCDReforged
cd release
echo %name% release maker
set /p ver=
rd /S /Q %name%
git clone https://github.com/Fallen-Breath/%name%.git
echo =========== Finish version update ===========

rd /S /Q %name%-%ver%
mkdir __temp__
cp -r %name% __temp__
mv __temp__\%name% %name%-%ver%
rd /S /Q __temp__
cd %name%-%ver%
rd /S /Q .git __pycache__ build
rm -f %name%.spec .gitignore
cd ..
rm -f %name%-%ver%-universal.zip
zip -r %name%-%ver%-universal.zip %name%-%ver%
echo =========== Finish universal version ===========

cd %name%
rm -rf dist
rm -rf build
rm -rf dist
pyinstaller --noupx -F %name%.py
cd ..
rd /S /Q %name%-%ver%
mv %name%\dist %name%-%ver%
cp %name%\config.yml %name%-%ver%\
cp %name%\readme.md %name%-%ver%\
cp %name%\readme_cn.md %name%-%ver%\
cp -r %name%\doc %name%-%ver%\
rm -f %name%-%ver%-windows.zip
zip -r %name%-%ver%-windows.zip %name%-%ver%
rd /S /Q %name%-%ver%
echo =========== Finish windows version ===========

rd /S /Q %name%
pause