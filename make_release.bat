set name=MCDReforged
mkdir release
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
rm -f %name%.spec .gitignore make_release.bat
mkdir server
cp doc\* .
rm -f plugins\*
rd /S /Q doc
cd ..
rm -f %name%-%ver%.zip
zip -r %name%-%ver%.zip %name%-%ver%

echo =========== Finish ===========

rd /S /Q %name%-%ver%
rd /S /Q %name%
pause