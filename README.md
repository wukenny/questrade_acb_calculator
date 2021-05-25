# What is is abc_calculator
To calculate ACB from Excel export of Questrade transactions

# How to run the program
Example:
```
./acb_calculator.py --input_file=/home/chi/python/margin_2020.xlsx
```
# Known issues
* Currency setting
	* Right now the program doesn't differentiate USD or CAD.
* Multiple files
	* Before running the code, merge all the Excel files into one first. 
	* Currently the script only checks one excel file. 
* Transitions of the same equity buy and sell occurred on the same day.
	* The order of buy and sell matters when calculating ACB and capital gain/loss
	* Questrade excel file for activities of the same equity does NOT guarantee the precise order
	* it has only the transaction date. 

# Calculation method 	
* Here we sort on a composite key of [date, transaction side, price, quantity]
* The purpose is to make it consistent to calculate ACB and capital across different years. 
* It might vary a bit within a year but should be consistent across years as long as you use the same order (sorting) when calculate carry-over from the previous# years.
* The code needs to alert if there are multiple transaction not one side only, happened on the same day for the same symbol.

# Future improvement
* The main method can be updated to scan multiple excel files under a directory
* Get Fx rate from internet and calculate settlement in CAD
