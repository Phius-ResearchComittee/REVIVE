"""insert your copyright here.

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/
"""

import typing

import openstudio


class NewMeasure(openstudio.measure.ModelMeasure):
    """Phius Multfamily Setup Measure"""

    def name(self):
        """Returns the human readable name.

        Measure name should be the title case of the class name.
        The measure name is the first contact a user has with the measure;
        it is also shared throughout the measure workflow, visible in the OpenStudio Application,
        PAT, Server Management Consoles, and in output reports.
        As such, measure names should clearly describe the measure's function,
        while remaining general in nature
        """
        return "Phius Multfamily Setup Measure"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "This measure sets up geometry of an OpenStudio model for Phius simulations. MELs, Lighting, Occupants, Appliances, Infiltration will all be set up per Phius modeling protocol."

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Comming soon..."

    def arguments(self, model: typing.Optional[openstudio.model.Model] = None):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        fridge_demand = openstudio.measure.OSArgument.makeDoubleArgument("fridge_demand", True)
        fridge_demand.setDisplayName("Annual Refridgerator Electrical Demand")
        fridge_demand.setDescription("Enter the annual energy demand for unit refridgerators in kWh/yr")
        fridge_demand.setDefaultValue(450)
        args.append(fridge_demand)

        dishwasher_demand = openstudio.measure.OSArgument.makeDoubleArgument("dishwasher_demand", True)
        dishwasher_demand.setDisplayName("Annual Dishwaser Electrical Demand")
        dishwasher_demand.setDescription("Enter the annual energy demand for unit dishwashers in kWh/yr")
        dishwasher_demand.setDefaultValue(269)
        args.append(dishwasher_demand)


        return args

    def run(
        self,
        model: openstudio.model.Model,
        runner: openstudio.measure.OSRunner,
        user_arguments: openstudio.measure.OSArgumentMap,
    ):
        """Defines what happens when the measure is run."""
        super().run(model, runner, user_arguments)  # Do **NOT** remove this line

        if not (runner.validateUserArguments(self.arguments(model), user_arguments)):
            return False

        # assign the user inputs to variables
        fridge_demand = runner.getDoubleArgumentValue("fridge_demand", user_arguments)

        # check the example_arg for reasonableness
        if not fridge_demand:
            runner.registerError("Empty space name was entered.")
            return False

        # report initial condition of model
        runner.registerInitialCondition(f"The building started with {len(model.getSpaces())} spaces.")
        spaces = model.getSpaces()
        
        print('Hello2')
        new_fridge = openstudio.model.ElectricEquipment.setElectricEquipmentDefinition(1)
        print(new_fridge)
        # add a new fridge to the model(
        for space in spaces:
            print(space.name)
            # new_fridge = openstudio.model.ElectricEquipmentDefinition()
            # new_fridge.setSchedule('Refridgerator Schedule')
            # new_fridge.setName('Refridgerator')
            # new_fridge.set

        # echo the new space's name back to the user
        # runner.registerInfo(f"Space {new_fridge.nameString()} was added.")

        # report final condition of model
        runner.registerFinalCondition(f"The building finished with {space.name} spaces.")

        return True


# register the measure to be used by the application
NewMeasure().registerWithApplication()
