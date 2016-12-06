'''
Description
This class takes a gui interface as an intit param, extracts the
neLineRegress paramater values from the the interface, and uses
them to write a config file that can be used by the neLineRegress program(s)>
'''
__filename__ = "pglineregressconfigfilemaker.py"
__date__ = "20161115"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from ConfigParser import ConfigParser
import os 
import pgutilities as pgut

class PGLineRegressConfigFileMaker( object ):

	CONFIG_FILE_EXT=".viz.config"
	'''
	In the Gui, in order to preserve unique
	attribute names, the viz attributes
	are in 4 parts, delimted.  The name
	that will be recognized by the viz
	program (hence to be written to 
	the config file) is the fourth item,
	and the third gives the config file
	section name in which the 4th item 
	resides.
	'''
	GUI_ATTRIBUTE_DELIMIT="_"
	IDX_GUI_ATTRIB_CONFIG_FILE_SECTION=2
	IDX_GUI_ATTRIB_CONFIG_FILE_PARAM=3


	def __init__( self, o_gui_interface ):

		self.__interface=o_gui_interface
		self.__ds_interface_param_values_by_param_names_by_section={}
		self.__mangled_attribute_prefix=None
		self.__config_outfile_name=None
		self.__config_parser_object=None
		
		self.__make_mangled_attribute_prefix()
		self.__make_dict_interface_param_values()
		self.__make_outfile_name()
		self.__make_parser_object()
		return
	#end __init__

	def __make_mangled_attribute_prefix( self ):
		'''
		I can't use the simpler type() method to
		get the class name, becuase the (grand)parent 
		Frame class (must be) old style, hence no metadata
		for type().  I instead use this tortured bit of code
		'''
		s_gui_class_name=( self.__interface ).__class__.__name__ 

		self.__mangled_attribute_prefix= \
				"_"  + s_gui_class_name + "__"
		return
	#end __make_mangled_attribute_prefix

	def __make_dict_interface_param_values( self ):
		ls_interface_member_names=dir( self.__interface )
	
		#GUI interface members for viz all begin
		#with this prefix--we need the trailing delimiter
		#because a generel attribute "viztype" is used only 
		#by the GUI (not a plotting param)
		s_viz_prefix=self.__mangled_attribute_prefix + "viz" \
					+ PGLineRegressConfigFileMaker.GUI_ATTRIBUTE_DELIMIT
		for s_member_name in ls_interface_member_names:

			if s_member_name.startswith( s_viz_prefix ):
				#strip off the mangling:
				s_member_name_unmangled=s_member_name.replace( self.__mangled_attribute_prefix, "" )

				#Extract the param name (used by the viz program):
				ls_member_name_parts=s_member_name_unmangled.split( \
						PGLineRegressConfigFileMaker.GUI_ATTRIBUTE_DELIMIT )
				s_viz_section_name=ls_member_name_parts[ \
						PGLineRegressConfigFileMaker.IDX_GUI_ATTRIB_CONFIG_FILE_SECTION ]
				s_viz_param_name=ls_member_name_parts[ \
						PGLineRegressConfigFileMaker.IDX_GUI_ATTRIB_CONFIG_FILE_PARAM ] 
				v_value_this_param = getattr( self.__interface, s_member_name )

				if s_viz_section_name not in self.__ds_interface_param_values_by_param_names_by_section:
					self.__ds_interface_param_values_by_param_names_by_section[ s_viz_section_name ] = {}
				#end if section name new to dict, add it

				self.__ds_interface_param_values_by_param_names_by_section[ s_viz_section_name ] [ \
															s_viz_param_name ] = v_value_this_param

			#end if the member is a viz param

		#end for each member of the interface
		return
	#end __make_dict_interface_param_values

	def __make_outfile_name( self ):
		o_strvar_outputdir=getattr( self.__interface, 
				self.__mangled_attribute_prefix \
								+ "output_directory" )

		s_outputdir=o_strvar_outputdir.get()

		s_outfile_basename=self.__interface.output_base_name

		if pgut.is_windows_platform():
			s_outputdir=pgut.fix_windows_path( s_outputdir )
			'''
			In case the GUI user entered a path separator into
			the basename entry
			'''
			s_outfile_basename=pgut.fix_windows_path( s_outfile_basename )
		#end if windows platform
		
		self.__config_outfile_name= \
				s_outputdir + "/" + s_outfile_basename \
				+ PGLineRegressConfigFileMaker.CONFIG_FILE_EXT
		return
	#end __make_outfile_name

	def __make_parser_object( self ):
		o_parser=ConfigParser()
		o_parser.optionxform=str

		for s_section in self.__ds_interface_param_values_by_param_names_by_section:
			o_parser.add_section( s_section )
			dv_param_values_by_param_name=self.__ds_interface_param_values_by_param_names_by_section[ s_section ]
			for s_param_name in dv_param_values_by_param_name:
				v_value_this_param=dv_param_values_by_param_name[ s_param_name ]
				o_parser.set( s_section, s_param_name, v_value_this_param )
			#end for each param (option, in config file parlance), in this section
		#end for each section

		self.__config_parser_object=o_parser

		return
	#end __make_parser_object

	def writeConfigFile( self ):
		if self.__config_parser_object is not None:

			if os.path.exists( self.__config_outfile_name ):
				s_msg="In PGLineRegressConfigFileMaker instance, "  \
							+ "def, __write_config_file.  The file, " \
							+ self.__config_outfile_name + ", " \
							+ "already exists.  This class disallows " \
							+ "overwriting exisiting files."
				raise Exception( s_msg )

			#end if file exists

			o_file=open( self.__config_outfile_name, 'w' )
			self.__config_parser_object.write( o_file )
			o_file.close()
		else:
			s_msg="In PGLineRegressConfigFileMaker instance, "  \
						+ "def, __write_config_file, an existing " \
						+ "parser object is required to write " \
						+ "the config file.  Found a None value for the " \
						+	"confg_parser_object member." \

			raise Exception( s_msg )
		#end if we have a config parser object else not

		return
	#end def write_config_file

	@property
	def config_file_name( self ):
		return self.__config_outfile_name
	#end property config_file_name
#end class PgLineRegressConfigFileMaker

if __name__ == "__main__":
	pass
#end if main
