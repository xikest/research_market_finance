from zipline.data.bundles import register, us_etfs, us_snp500

register('us_etfs', us_etfs.bundle_data, calendar_name='NYSE')
register('us_snp500', us_snp500.bundle_data, calendar_name='NYSE')