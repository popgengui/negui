'''
Description
Provides a panel and frame inside of which
to show a the table generated by pgregressionstats.py,
as well as a save button and dialog by which clients
can save the table to file.
'''

from __future__ import print_function
from future import standard_library

standard_library.install_aliases()

__filename__ = "pgregresstableshower.py"
__date__ = "20171016"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

from tkinter import *
from tkinter.ttk import *
import tkinter.scrolledtext as tkst
import tkinter.filedialog as tkfd

class PGRegressTableTextFrame( Frame ):
	'''
	Provides a panel and frame inside of which
	is shown a the table generated by pgregressionstats.py,
	as well as a save button and dialog by which clients
	can save the table to file.
	'''

	def __init__( self, o_master=None, 
							o_regress_table=None, 
							i_text_widget_width=40, 
							i_text_widget_height=20,
							b_file_name_only_in_stats_table_col_1=True ):
		'''
		Arg o_regress_table is an instance of PGRegressionStats.
		'''

		Frame.__init__( self, o_master )		

		self.__master_frame=o_master
		self.__table=o_regress_table
		self.__text_widget_width=i_text_widget_width
		self.__text_widget_height=i_text_widget_height
		self.__use_file_name_only_in_stats_table_column_1=\
					b_file_name_only_in_stats_table_col_1

		self.__get_text()

		self.__setup()
		return
	#end __init__

	def __get_text( self ):

		s_table="No data"

		if self.__table is not None:
			s_table=self.__table.getStatsTableAsString( \
						self.__use_file_name_only_in_stats_table_column_1 )
		#end if table is not None

		return s_table
	#end __get_text

	def __setup( self ):

		s_table_text=self.__get_text()

		o_scrolledtext=tkst.ScrolledText( self, wrap="word", 
									width=self.__text_widget_width, 
									height=self.__text_widget_height )

		o_scrolledtext.insert( "end", s_table_text )
		o_scrolledtext.configure( state="disabled" )
		o_scrolledtext.bind( "<1>", lambda event: o_scrolledtext.focus_set() )

		self.__scrolled_text=o_scrolledtext

		o_button=Button( self, text="Save to file", 
						command=self.__on_save_button_click )

		
		o_scrolledtext.grid(  row=0, column=0, sticky=(N,E,S,W) )
		o_button.grid(  row=1, column=0 )

		self.__save_button=o_button

		return
	#__setup

	def __on_save_button_click( self, o_event=None ):
		self.__save_text_widget_contents_to_file()
		return
	#end __on_save_button_click

	def __save_text_widget_contents_to_file( self ):
		if self.__scrolled_text is not None:
			o_outputfile=tkfd.asksaveasfile( \
					title='Save text to file' )
			#if no dir selected, return	

			if o_outputfile is None:
				return
			else:
				o_outputfile.write( self.__scrolled_text.get(1.0, END) )
				o_outputfile.close()
			#end if plotframe exists	
		#end if no dir selected
		return
	#end __save_text_widget_contents_to_file

	def saveTextToFile( self ):
		self.__save_text_widget_contents_to_file()
		return
	#end saveTextToFile

	def updateTextWidgetContents( self ):
		s_text=self.__get_text()
		if self.__scrolled_text is not None:
			self.__scrolled_text.configure( state=NORMAL )
			self.__scrolled_text.delete( 1.0, END )
			self.__scrolled_text.insert( END, s_text )
		#end if we have a text widget
		return
	#end updateTextWidgetContents

	def useFileNameOnlyInStatsTableCol1( self, b_true_or_false ):
		self.__use_file_name_only_in_stats_table_column_1=b_true_or_false
	#end setFlagUseAllFieldsInStatsTableCol1
#end class PGRegressTableTextFrame

if __name__ == "__main__":

	import agestrucne.pgneestimationtablefilemanager as pgfm
	from agestrucne.pgregressionstats import PGRegressionStats
	mymaster=Tk()

	s_tsv_file="/home/ted/documents/source_code/python/negui/temp_data/frogs.estimates.ldne.tsv"

	o_regressstatsgetter=PGRegressionStats()

	MYKEYS=pgfm.NeEstimationTableFileManager.INPUT_FIELDS_ASSOC_WITH_ONE_ESTIMATE

	MYKEYS.remove( 'pop' )

	o_tsv_file_manager=pgfm.NeEstimationTableFileManager( s_tsv_file )

	dlsresults=o_tsv_file_manager.getDictDataLinesKeyedToColnames( ls_key_column_names=MYKEYS, 
											ls_value_column_names=[ "pop", "ne_est_adj" ],
											b_skip_header=True )

	o_regressstatsgetter.setTsvFileManagerDictAsTable( dlsresults )
	
	ome=PGRegressTableTextFrame( o_master=mymaster, o_regress_table=o_regressstatsgetter,
					i_text_widget_width=100, i_text_widget_height=30)

	ome.grid()

	mymaster.mainloop()
	pass
#end if main

