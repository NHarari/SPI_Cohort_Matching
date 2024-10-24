class QueryClass():

    def __init__(self):
        """
        no variables to initialize yet 
        """
    
    def query_spi_events(self, start_year, customer_list):

        q = f"""
              SELECT distinct pmc.person_id
              , pmc.drvd_mbrshp_covrg_id
              , sd.utc_period
              , case when sd.savings_category in 
                     ('High Cost Claimants (HCC)', 'Case Management', 'Disease Management',
                     'Maternity Program', 'Treatment Decision Support') then sd.savings_category
                     else 'other_SPI_event' end as category
             , 'spi_definition' as sub_category
              FROM acp_edw.info_layer.v1_uat_spi_dtl sd
              inner join acp_edw.info_layer.prs_mbrshp_covrg pmc on 
                     upper(sd.drvd_mbrshp_covrg_id) = upper(pmc.drvd_mbrshp_covrg_id) and 
                     sd.utc_period = pmc.utc_period
              WHERE left(sd.utc_period,4) >= '{start_year}' 
              AND pmc.org_nm in ('{customer_list}')
              """
              
        return q
    
    def query_hcc_clinical_events(self, start_year, customer_list):

        q = f"""
                with #first_hcc as (select distinct prs.drvd_mbrshp_covrg_id        as hcc_id
                                                , prs.person_id
                                                , left(ca.adjudication_period, 4) as hcc_yr
                                                , min(ca.adjudication_period)     as hcc_mo
                                    from acp_edw.info_layer.prs_mbrshp_covrg prs
                                            join acp_edw.info_layer.v1_uat_svc_ytd_mbr_clms_agg ca
                                                on prs.drvd_mbrshp_covrg_id = ca.drvd_mbrshp_covrg_id and
                                                    prs.utc_period = ca.adjudication_period
                                    where ca.hcc_flg = true
                                    and prs.acp_mbr_flg = 1
                                    and left(prs.utc_period, 4) >= '{start_year}' 
                                    and prs.org_nm in ('{customer_list}')
                                    group by 1, 2, 3)
                , #first_clin_eng as (select distinct mc.drvd_mbrshp_covrg_id as eng_id
                                                    , left(mc.utc_period, 4)  as eng_yr
                                                    , min(mc.utc_period)      as eng_mo
                                        from acp_edw.info_layer.mstr_comm mc
                                                inner join acp_edw.info_layer.task_dtl td ON td.enctr_id = mc.enctr_id AND
                                                                                    td.task_cd = 'issue' AND
                                                                                    td.task_sts NOT IN
                                                                                    ('duplicate', 'rejected', 'cancelled',
                                                                                        'entered-in-error', 'draft') AND
                                                                                    td.deleted_flg <> 1 AND
                                                                                    td.objtv_category = 'Care' AND
                                                                                    (td.objtv_type_nm = 'Other Care Education') is false
                                        WHERE mc.clinical_engmnt_flg = 1
                                        and left(mc.utc_period, 4) >= '{start_year}' 
                                        and mc.drvd_org_nm in ('{customer_list}')
                                        group by 1, 2)
                select fc.person_id
                    , fc.hcc_id as drvd_mbrshp_covrg_id
                    , fe.eng_mo as utc_period
                    , 'HCC Clinical Eng' as category
                    , case when hcc_mo > fe.eng_mo then 'pre-hcc'
                            else 'post-hcc' end as sub_category
                from #first_hcc fc
                        inner join #first_clin_eng fe on fc.hcc_id = fe.eng_id and fc.hcc_yr = fe.eng_yr
                """

        return q
    
    def query_funnel(self, start_year, customer_list):
        
        q = f""" select distinct cfd.person_id
                            , cfd.drvd_mbrshp_covrg_id
                            , cfd.utc_period
                            , cfd.pgrm_nm as category
                            , case
                                    when ji.enc_idn is null then 'no_jiva'
                                    else 'jiva_close' end as sub_category
                from acp_edw.info_layer.v1_uat_clinical_funnel_dtl cfd
                        left join acp_edw.edw.lnk_care_pln_alt_id alt
                                on alt.care_pln_id = cfd.care_pln_id and alt.alt_id_sys = 'https://zeomega.com/jiva-episode-idn'
                        left join acp_edw.edw.jiva_v_model_interventions ji
                                on ji.enc_idn = alt.alt_id_val and ji.intervention_status = 'Closed'
                where cfd.closed_dtm is not null
                and cfd.enrolled_dtm is not null
                and (cfd.pgrm_nm like ('%BH%')) is false
                and (cfd.pgrm_nm like ('%NICU%')) is false
                and (cfd.pgrm_nm like ('%Pediatric%')) is false
                and cfd.pgrm_nm not in ('Symptoms Care', 'Pharmacy', 'MSK', 'MHIC', 'Conditions Care')
                and left(utc_period, 4) >= '{start_year}' 
                and cfd.org_nm in ('{customer_list}')
                """
        
        return q
    
    def query_eng_events(self, start_year, customer_list):

        q = f"""with #first_eng as (select prs.person_id
                                        , prs.drvd_mbrshp_covrg_id
                                        , left(mc.utc_period, 4) as eng_yr
                                        , min(mc.utc_period)     as eng_mo
                                    from acp_edw.info_layer.mstr_comm mc
                                            join acp_edw.info_layer.prs_mbrshp_covrg prs
                                                on upper(mc.drvd_mbrshp_covrg_id) = upper(prs.drvd_mbrshp_covrg_id)
                                    where mc.engmnt_flg = true
                                    and mc.utc_period >= '{start_year}' 
                                    and mc.drvd_org_nm in ('{customer_list}')
                                    group by 1, 2, 3)
                select person_id
                    , drvd_mbrshp_covrg_id
                    , eng_mo    as utc_period
                    , 'Engaged' as category
                from #first_eng
                """

        return q
        
    def query_crosswalk(self, start_year, customer_list):
           
        q = f"""
              SELECT distinct pmc.org_nm
              , pmc.person_id
              , pmc.utc_period
              from acp_edw.info_layer.prs_mbrshp_covrg pmc
              WHERE left(utc_period,4) >= '{start_year}' 
              AND pmc.org_nm in ('{customer_list}')
              """

        return q
