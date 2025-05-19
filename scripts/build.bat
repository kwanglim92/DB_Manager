@echo off
echo Building DB Compare Tool...

:: 상위 디렉토리로 이동
cd ..

:: 이전 빌드 정리
rmdir /s /q build
rmdir /s /q dist

:: exe 파일 생성
pyinstaller --onefile ^
            --windowed ^
            --icon="resources\icons\db_compare.ico" ^
            --add-data "resources\icons\db_compare.ico;resources\icons" ^
            --name="DB Compare Tool" ^
            --version-file=resources\version_info.txt ^
            src\DB_Manager.py

:: 결과물 이동
mkdir dist\v1.0.0
move "dist\DB Compare Tool.exe" "dist\v1.0.0\"

echo Build completed! Check the dist/v1.0.0 folder.
pause