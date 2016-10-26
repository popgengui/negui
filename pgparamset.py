'''
Description

Class ParamSet is used to associate
parameter names as given by code variables
(called class attribute shortname),
each with a more user-friendly
name.  These long names (attribute longname) are used
for example, as labels in the gui interface
that allows  users to set the parameters.

2016_09_08
Over last few weeks have added fields to the "tag"
column in the paramset files, read by objects of
this class.  There are now many sub-fields inside
the tag that are used to get a default value, 
type the value, add a tool tip, and give a max
and min value for validation.

Sat Sep 24 20:02:31 MDT 2016
Have collapsed the "longname" item into the tag,
so that now the file should contain only two
tab-delimited fields, the parameter name, 
and the tag of semi-colon delimited fields,
one of which is now the longname.

'''
__filename__ = "pgparamset.py"
__date__ = "20160429"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

class PGParamSet( object ):

	'''
	Class ParamSet is used to replace
	parameter names as given by code variables
	and associates each with a more user-friendly
	name.  These longer, fuller names are used
	for example, as labels in the gui interface
	that allows users to set the parameters.

	2016_09_08
	Over last few weeks have added fields to the "tag"
	column in the paramset files, read by objects of
	this class.  There are now many sub-fields inside
	the tag that are used to get a default value, 
	type the value, add a tool tip, and give a max
	and min value for validation.  See the IDX_ declarations
	below for order and meaning of these tag "subfields"

	2016_09_24
	The longname item has been moved into the tag, so that now
	only two columns are given in the paremeter file.

	'''

	DELIMITER_TAG_FIELDS=";"
	IDX_PARAM_SHORTNAME=0
	IDX_PARAM_TAG=1
	PARAM_FIELDS_TOTAL=2

	'''
	Below indices refer to the semicolon delimited
	fields in the tag column. This zeroth index
	gives the long name of the param
	'''
	IDX_TAG_FEILD_LONGNAME=0

	'''
	interface secion, which is a collection of parameters
	as framed and set apart from the others.
	'''
	IDX_TAG_FIELD_CONFIG_SECTION=1

	'''
	Gives the GUI placement order of the section.
	Assumes all sections are in a single column.
	'''
	IDX_TAG_FIELD_CONFIG_SECTION_PLACEMENT_ORDER=2

	'''
	Gives the GUI placement column number ( inside the
	section) for the parameter.
	'''
	IDX_TAG_FIELD_COLUMN_NUMBER=3

	'''
	Gives the the vertical order of placement
	for the parameter inside the section.
	'''
	IDX_TAG_FIELD_PARAM_ORDER=4

	'''
	The default value for the parameter. 
	'''
	IDX_TAG_FIELD_DEFAULT_VALUE=5

	'''
	The parameter type.  As of 2016_09_21, these include
	int, float, str, or list.  
	'''
	IDX_TAG_FIELD_PARAM_TYPE=6

	'''
	Especially for numeric types, the minimum
	allowed value.  For strings, this gives
	the minimum length allowed.
	'''
	IDX_TAG_FIELD_MIN_VALUE=7

	'''
	As for the above MIN value, but 
	for maximum allowed.
	'''
	IDX_TAG_FIELD_MAX_VALUE=8

	'''
	The text to be used to create a
	mouse-over tool tip.
	'''
	IDX_TAG_FIELD_TOOL_TIP=9

	'''
	Gives the type of GUI control to be used
	to present the parameter for editing and/or
	visualizing.  As of 2016_09_21, possible entries
	are "entry" or "cbox" (combo box ).
	'''
	IDX_TAG_FIELD_GUI_CONTROL=10

	'''
	For combo box GUI controls, the list of strings
	to be used as choices in the combo box.
	'''
	IDX_TAG_FIELD_GUI_CONTROL_LIST=11

	'''
	Added 2016_10_03, a statement that when 
	concatenated with "lambda x: ", gives
	a def that will eval to true or false,
	as to whether the value x is valid.
	'''
	IDX_TAG_FIELD_VALIDATION=12

	'''
	Added 2016_10_16, if not None, this
	names a def, which must be present in
	the object to which it is assigned, and which
	can be passed to an KeyVal control (mostly
	KeyValFrame objects) giving a def to be called
	when a param value changes.
	'''
	IDX_TAG_FIELD_ASSOC_DEF=13

	COMMENT_CHAR="#"

	def __init__( self, s_file_with_param_names = None ):

		'''
		If provided, arg s_file_with_param_names
		should be a file with 2 or more strings on each line,
		tab-separated, the first value giving the short
		name of the parameter, the second the long (full)
		name, the third (if present)
		'''
		self.__file_with_param_names=s_file_with_param_names
		self.__tags_by_shortname={}

		if s_file_with_param_names is not None:
			self.__init_from_file( s_file_with_param_names )
		#end if file name given
		return
	#end __init__

	def __init_from_file( self, s_file_with_param_names ):
		o_file=open( s_file_with_param_names )

		for s_line in o_file:
			if s_line.startswith( PGParamSet.COMMENT_CHAR ):
				continue
			#end if comment

			s_tag=None
			ls_vals= s_line.strip().split( "\t" )

			try:

				s_shortname=ls_vals[ PGParamSet.IDX_PARAM_SHORTNAME ]

				self.__set_parameter( s_shortname)
				if len( ls_vals )>=PGParamSet.PARAM_FIELDS_TOTAL:
					s_tag=ls_vals[ PGParamSet.IDX_PARAM_TAG ] if ls_vals[ PGParamSet.IDX_PARAM_TAG ] != "None" else None
				#end if we have a 3rd string 
					
				self.__tags_by_shortname[ s_shortname ] = s_tag
				
			except Exception as oex:

				s_msg="In PGParamSet instance, def __init_from_file, " \
						+ "exception while parsing line, " \
						+ s_line  + ":\n" \
						+ "\nException: " + str( oex ) + "."

				raise Exception( s_msg )
			#end try . . . except
						
		#end for each line in file

		o_file.close()
		return
	#end __init_from_file

	def __get_tag_field( self, s_tag, i_idx ):

		ls_tag_values=s_tag.split( PGParamSet.DELIMITER_TAG_FIELDS )

		if len( ls_tag_values ) <= i_idx:
			s_msg="In PGParamSet instance, def get_tag_field, "  \
					+ "tag, \"" + s_tag \
					+ "\", has too few fields to retrieve index number: " \
					+ str( i_idx ) + "."			
			raise Exception( s_msg )
		#end if field list is too short

		s_field_val=ls_tag_values[ i_idx ]

		return s_field_val

	#end __get_tag_field

	#defs that fetch tag info given a tag string:

	def getLongnameFromTag( self, s_tag ):
		s_longname=self.__get_tag_field( s_tag,
					PGParamSet.IDX_TAG_FEILD_LONGNAME )
	#end getLongnameFromTag

	def getConfigSectionNameFromTag( self, s_tag ):
		s_section_name = self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_CONFIG_SECTION ) 
		return s_section_name
	#end getConfigSectionNameForParam

	def getDefaultValueFromTag( self, s_tag ):
		s_default_val_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_DEFAULT_VALUE )
		return s_default_val_as_string
	#end getDefaultValueFromParamTag

	def getSectionOrderFromTag( self, s_tag ):
		s_section_order_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_CONFIG_SECTION_PLACEMENT_ORDER )
		return s_section_order_as_string
	#end getSectionOrderFromParamTag

	def getSectionColNumFromTag( self, s_tag ):
		s_section_col_num_as_string=self.__get_tag_field( s_tag,
									PGParamSet.IDX_TAG_FIELD_COLUMN_NUMBER )
		return s_section_col_num_as_string
	#end getSectionColNumFromTag

	def getParamOrderNumberFromTag( self, s_tag ):
		s_section_param_order_as_string=self.__get_tag_field( s_tag,
									PGParamSet.IDX_TAG_FIELD_PARAM_ORDER )
		return s_section_param_order_as_string
	#end getSectionColNumFromTag

	def getToolTipFromTag( self, s_tag ):
		s_tool_tip=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_TOOL_TIP )
		return s_section_param_order_as_string
	#end getSectionColNumFromTag

	def getParamTypeFromTag( self, s_tag ):
		s_type_as_string=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_PARAM_TYPE )
		return s_type_as_string
	#end getParamTypeFromTag

	def getParamMinFromTag( self, s_tag ):
		s_min_as_string=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_MIN_VALUE )
		return s_min_as_string
	#end getParamMinFromTag

	def getParamMaxFromTag( self, s_tag ):
		s_max_as_string=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_MAX_VALUE )
		return s_max_as_string
	#end getParamMaxFromTag

	def getGUIControlFromTag( self, s_tag ):
		s_gui_control=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_GUI_CONTROL )
		return s_gui_control
	#defs that fetch tag info from param name:

	def getControlListFromTag( self, s_tag ):
		s_control_list=self.__get_tag_field( s_tag, 
					PGParamSet.IDX_TAG_FIELD_GUI_CONTROL_LIST )
		return s_control_list
	#end getControlListFromTag

	def getValidationFromTag( self, s_tag ):
		s_validation=self.__get_tag_field( s_tag,
					PGParamSet.IDX_TAG_FIELD_VALIDATION )
		return s_validation
	#end getValidationFromTag

	def getAssocDefFromTag( self, s_tag ):
		s_def=self.__get_tag_field( s_tag,
					PGParamSet.IDX_TAG_FIELD_ASSOC_DEF )
		return s_def
	#end getAssocDefFromTag

	def getConfigSectionNameForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_section_name = self.__get_tag_field( s_tag, 
								PGParamSet.IDX_TAG_FIELD_CONFIG_SECTION ) 
		return s_section_name
	#end getConfigSectionNameForParam

	def getDefaultValueForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_default_val_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_DEFAULT_VALUE )
		return s_default_val_as_string
	#end getDefaultValueForParam

	def getSectionOrderForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_section_order_as_string=self.__get_tag_field( s_tag, 
						PGParamSet.IDX_TAG_FIELD_CONFIG_SECTION_PLACEMENT_ORDER )
		return s_section_order_as_string
	#end getSectionOrderForParamTag

	def getParamOrderNumberForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_param_order_as_string=self.__get_tag_field( s_tag, 
									PGParamSet.IDX_TAG_FIELD_PARAM_ORDER )
		return s_param_order_as_string
	#end getParamOrderNumberForParam

	def getSectionColNumForParam( self, s_name ):
		s_tag=self.tag( s_name )	
		s_section_col_num_as_string=self.__get_tag_field( s_tag,
									PGParamSet.IDX_TAG_FIELD_COLUMN_NUMBER )
		return s_section_col_num_as_string
	#end getSectionColNumForParam

	def getToolTipForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_tool_tip=self.__get_tag_field( s_tag,
									PGParamSet.IDX_TAG_FIELD_TOOL_TIP )
		return s_tool_tip	
	#end getToolTipForParam

	def getParamTypeForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_type_as_string=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_PARAM_TYPE )
		return s_type_as_string
	#end getParamTypeForParam

	def getParamMinForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_min_as_string=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_MIN_VALUE )
		return s_min_as_string
	#end getParamMinForParam

	def getParamMaxForParam( self, s_name ):
		s_tag=self.tag( s_name)
		s_max_as_string=self.__get_tag_field( s_tag,
						PGParamSet.IDX_TAG_FIELD_MAX_VALUE )
		return s_max_as_string
	#end getParamMaxForParam

	def getGUIControlForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_gui_control=self.__get_tag_field( s_tag,
					PGParamSet.IDX_TAG_FIELD_GUI_CONTROL )
		return s_gui_control
	#end getGUIControlFromTag

	def getControlListForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_control_list=self.__get_tag_field( s_tag, 
					PGParamSet.IDX_TAG_FIELD_GUI_CONTROL_LIST )
		return s_control_list
	#end getControlListForParam

	def getLongnameForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_longname=self.__get_tag_field( s_tag,
					PGParamSet.IDX_TAG_FEILD_LONGNAME )
		return s_longname
	#end getLongnameForParam

	def getValidationForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_validation=self.__get_tag_field( s_tag,
					PGParamSet.IDX_TAG_FIELD_VALIDATION )
		return s_validation
	#end getValidationForParam

	def getAssocDefForParam( self, s_name ):
		s_tag=self.tag( s_name )
		s_def=self.__get_tag_field( s_tag, 
				PGParamSet.IDX_TAG_FIELD_ASSOC_DEF )
		return s_def
	#end getAssocDefForParam

	def tag( self, s_name ):
		'''
		param s_name can be either among the 
		short or long names (or both). Shortnames
		are checked first.  First instance of name
		provides its tag as the return value.
		'''
		s_val=None

		if s_name in self.__tags_by_shortname:
			s_val = self.__tags_by_shortname[ s_name ]
		else:
			s_msg="In PGParamSet instance, def tag(), no tag " \
					+ "associated with " \
					+ "param name, " + s_name + "."
			raise Exception ( s_msg )
		#end if tag in short else if tag in long

		return s_val
	#end tag
	def __set_parameter( self, s_shortname, s_tag=None ):
		
		
		if s_shortname in self.__tags_by_shortname:
			s_errmsg="In PGParamSet instance, def __set_parameter, " \
						+ "Object requires unique strings for parameter " \
						+ "short names.  At least two identical " \
						+ "parameter short names found for: " \
						+ s_shortname + "."
			raise Exception( s_errmsg )
		#end if non uniq shortname
					
		self.__tags_by_shortname[ s_shortname ] = s_tag

		return
	#end setParam

	def initFromFile( self, s_param_name_file ):
		self.__init_from_file( s_param_name_file )
		return
	#end initFromFile

	@property
	def param_names_file( self ):
		return self.__file_with_param_names
	#end param_names_file getter

	@property
	def longnames(self):

		ls_longnames=[]

		for s_name in self.__tags_by_shortname.keys():
			ls_longnames.append( \
					self.getLongnameForParam( s_name ) )
		#end for each param

		ls_longnames.sort()
		return ls_longnames
	#end longnames
			
	@property
	def shortnames(self):
		ls_shortnames=list( self.__tags_by_shortname.keys() )
		ls_shortnames.sort()
		return ls_shortnames
	#end shortnames

	@property
	def tags(self):
		'''
		returns a list of tags, without their associated
		param names (short or long).  Useful to get
		the set of unique tags if the tags categorize
		the paramset into groups
		'''
		ls_tags=self.__tags_by_shortname.values()
		ls_tags.sort()
		return ls_tags
	#end shortnames

	@property
	def section_names( self ):
	  ls_section_names=[ getConfigSectionNameForParam( s_param ) \
			  for s_param in self.shortnames ]
	#end section_names
#end class ParamSet

if __name__=="__main__":
	#original test code now broken
	#due to class changes
	pass
#end if run as main, then test

