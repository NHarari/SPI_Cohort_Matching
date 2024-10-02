import pandas as pd

class CG_Helper():

    def __init__(self):
        """
        no variables to initialize yet 
        """

    def map_customers(self, customer_df, column_nm):
                                        
        mapping = {"7-ELEVEN, INC.": "SEVEN ELEVEN",
                    "ABA EMPLOYEE SERVICES": "LIGHTHOUSE AUTISM CENTER",
                    "ADVANTAGE SALES AND MARKETING": "ADVANTAGE SOLUTIONS",
                    "AERA ENERGY SERVICES COMPANY": "AERA ENERGY",
                    "API GROUP, INC": "API GROUP",
                    "CALIFORNIA HIGHWAY PATROL": "CALIFORNIA ASSOCIATION OF HIGHWAY PATROLMEN",
                    "CENTERWELL": "CENTERWELL HOME HEALTH",
                    "COREWELL": "COREWELL HEALTH",
                    "EMD": "BENEFITS4ME",
                    "ENERCON SERVICES, INC.": "ENERCON",
                    "ENLYTE (FORMERLY MITCHELL-GENEX SERVICES)": "ENLYTE",
                    "FIRST AMERICAN FINANCIAL CORP": "FIRST AMERICAN FINANCIAL",
                    "FULL BLOOM": "CATAPULT",
                    "GENERAL MILLS, INC.": "GENERAL MILLS",
                    "GREIF PACKAGING": "GREIF INC",
                    "INTUIT INC.": "INTUIT",
                    "L3HARRISTECHNOLOGIESINC": "L3HARRIS",
                    "LAND O'LAKES, INC.": "LAND O'LAKES",
                    "LANDRY'S AND GOLDEN NUGGET": "LANDRYS INC",
                    "LASSONDE PAPPAS": "LASSONDE PAPPAS AND COMPANY",
                    "LOWES": "LOWE'S",
                    "PEPSI-COLA AND NATIONAL BRAND BEVERAGES": "HONICKMAN",
                    "PRISM/CITY OF REDDING": "CITY OF REDDING",
                    "PRISM/COUNTY OF SANTA BARBARA": "COUNTY OF SANTA BARBARA",
                    "RACETRAC PETROLEUM, INC.": "RACETRAC",
                    "RED RIVER TECHNOLOGY LLC": "RED RIVER TECHNOLOGY",
                    "TEMPLE UNIVERSITY HEALTH SYSTEM": "TEMPLE",
                    "TUTOR PERINI CORPORATION": "TUTOR PERINI",
                    "UGI": "AMERIGAS",
                    "UNISYS CORPORATION": "UNISYS"
                }
        
        customer_df['edw_cust']  = customer_df[column_nm].str.upper().map(mapping).fillna(customer_df[column_nm].str.upper())

        return customer_df
                
    def map_customers_schema(self, customer_df, schema_df):
               
        customer_df = self.map_customers(self, customer_df, 'cg_cust')
        customer_df = customer_df.merge(schema_df, on='acronym')
        
        #remove the extra lines
        customer_df = customer_df[~customer_df['edw_cust'].isin(['BK', 'NON-ACCOLADE', 'ACCOLADE', 'BLANK'])]
        
        #mark the schemas with multiple customers
        schema_cust = customer_df.groupby('table_schema')['edw_cust'].nunique().reset_index().rename(columns={'edw_cust':'num_cust'})
        customer_df = customer_df.merge(schema_cust, on='table_schema')
        
        #return
        return customer_df[['table_schema', 'acronym', 'edw_cust', 'cg_cust', 'num_cust']]
        
        