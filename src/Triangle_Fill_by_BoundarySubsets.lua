--------------------------------------------------------------------------------
-- Lua-Script for ProMesh4
-- The variable 'mesh' contains the mesh object on which the script shall operate
-- The pm-declare- comments define the resutling tool's name ('pm-declare-name')
-- and the script's input parameters ('pm-declare-input'). Sample names and
-- parameters are provided. They can be erased or changed as required.
--
-- 'pm-declare-input' has the following sections, each separated by '|':
--		1: the name under which the input-parameter is accessible in the script
--		2: the name of the input-parameter as it appears in promesh
--		3: the type of the input-value (double, integer, boolean, string)
--		4: default-, minimal- and maximal-values, number of digits (only double)
--		   and the step-size, which defines how much a value is increased or
--		   decreased when the up/down arrows are pressed. The different values
--		   can be set through 'val', 'min', 'max', 'digits', and 'step'. If more
--		   than one value is specified, they have to be separated by ';'.
--
-- If you're editing a script while ProMesh is running, press
-- Scripts-RefreshToolDialogs to update the associated tools content.
--------------------------------------------------------------------------------

-- pm-declare-name: Triangle Fill by known Boundary Subsets
-- pm-declare-input: delimiter | delimiter | string | val=/
-- pm-declare-input: angle | angle | double | val = 20; min = 10; max = 45; digits = 2; step = 0.1
-- pm-declare-input: quality | quality | boolean | val = true
-- pm-declare-input: allTarget | all | boolean | val=true
-- pm-declare-input: targetArea | specific target | string | val=nil



sh=mesh:subset_handler()
size=sh:num_subsets()



------------------------------------------------------------------------------------
---- Create a table *allSubsetNames*  to store all subset names(with delimiters) 
local subsetIndexes = {}
local allSubsetNames = {}
for i=0, size-1 do
	local subNa = sh: get_subset_name(i)
end



----- Create a table *allName* to store all separate names  
local pattern = '[^' .. delimiter .. ']+'
local allName = {}
for i=0, size-1 do
    	local subNa = sh: get_subset_name(i)  
    	if string.find(subNa,delimiter) then      
        		for part in subNa:gmatch(pattern) do	   
            		table.insert(allName, { name = part, subNa = subNa })
        		end
    	else
        		table.insert(allName,{ name = subNa, subNa = subNa })
    	end
end


----- Create a table *uniqueAllName* to store all separated unique names  
local uniqueAllName = {}
for _,entry in ipairs(allName) do
    	local name = entry.name
    	if not uniqueAllName[name] then
        		uniqueAllName[name]= true
    	end
end



------  assign each unique name its corresponding index that has not appeared before (allSubsetNames) 
local index = size-1
for uniName, _ in pairs(uniqueAllName) do
    	local found = false
    	for _, subsetName in ipairs(allSubsetNames) do
        		if subsetName == uniName then
            		found = true
            		break
        		end
    	end
    	if not found then
        		index = index + 1  
        		AssignNewSubset (mesh, uniName, true, true, true, true)
        		subsetIndexes[uniName] = index  
    	end
end


------ Find all relevant edges corresponding to the unique name
function findRelevantAllEdges(name)	
	local index = subsetIndexes[name]
	if index then
                local entrySub = {}
                for _, entry in ipairs(allName) do
                    if entry.name == name then
                        table.insert(entrySub, entry.subNa)
                    end
                end
                
                for _, sub in ipairs(entrySub) do
                    local si = sh:get_subset_index(sub)
                    SelectSubset(mesh, si, true, true, true, true)
                end
                
                TriangleFill(mesh, quality, angle, index)
                ClearSelection(mesh)
           else
                print("Invalid choice. Please choose a specific area from uniqueAllName.")
            
           end       
end


----- Choose whether to triangle fill the entire map or a specific part.
if allTarget  then
    for name, _ in pairs(uniqueAllName) do
        local index = subsetIndexes[name]
        if index then
            local entrySub = {}
            local countPrints = 0
            local hasZeroArea = false
            local nosub = false

            for _, entry in ipairs(allName) do
                if entry.name == name then
                    countPrints = countPrints + 1
                    table.insert(entrySub, entry.subNa)
                end
            end

            for _, sub in ipairs(entrySub) do
                local si = sh:get_subset_index(sub)
                SelectSubset(mesh, si, true, true, true, true)
                if sub ~= name then
                    nosub = true
                else
                    nosub = false
                end
            end

            if countPrints == 1 and nosub then
                hasZeroArea = true
                print('Maybe the area of ' .. name .. ' is 0')
            end

            if not hasZeroArea then
                TriangleFill(mesh, quality, angle, index)
                ClearSelection(mesh)
            end
            ClearSelection(mesh)
        end
    end
    
else
    if string.find(targetArea, delimiter) then
        for part in string.gmatch(targetArea, '([^' .. delimiter .. ']+)') do
	    findRelevantAllEdges(part)
        end
        
     else 
	findRelevantAllEdges(targetArea)
      end
end

AssignSubsetColors(mesh)









