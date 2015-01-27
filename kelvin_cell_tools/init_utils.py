def write_inital_conditions(folder,massfraction,velocity,temperature):

    import kelvin_cell_tools.initial_condition_writer as ini
    writer = ini.initalconditions_writer()
    writer.add_variable("uvelocity",velocity)
    writer.add_variable("temperature",temperature)
    
    for key,item in massfraction.iteritems():
        writer.add_variable(var="component_molefraction",value=item[0],index=item[1])
        
    writer.write_file(folder)
    
