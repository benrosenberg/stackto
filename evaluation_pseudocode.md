# Pseudocode for StackTo program evaluation

```
function process_statements(statements) is
	vars := dict
	markers := dict

	// identify marker indices
	index := 0
	while index < len(statements) do
		if statement is MARK(marker) then
			markers[marker] = index
		endif
	endwhile

	// evaluate program within context of marker indices
	index := 0
	while index < len(statements) do
		if statement is OUTPUT(varname) then
			output vars[varname]
		endif
		if statement is OUTPUT(expression) then
			value := parse expression
			output value
		endif
		if statement is MARK(marker) then
			continue
		endif
		if statement is SET(varname, expression) then
			value := parse expression
			vars[variablename] := value
		endif
		if statement is GOTO(marker) then
			index := markers[marker]
		endif
		if statement is IF(expression, ifbody) then
			guard_value := parse expression
			if guard_value is true then
				if ifbody is SET(varname, expression) then
					value := parse expression
					vars[variablename] := value
				endif
				if ifbody is GOTO(marker) then
					index := markers[marker]
				endif
				if statement is OUTPUT(varname) then
					output vars[varname]
				endif
				if statement is OUTPUT(expression) then
					value := parse expression
					output value
				endif
			endif
		endif
	endwhile
end
```