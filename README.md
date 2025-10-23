### ESOUI Downloads

This project consists of two parts - a data pipeline and a website. The data pipeline is designed to periodically take snapshots of current download values of all addons posted on [ESOUI](https://www.esoui.com/community.php) and load them to a PostgreSQL database. The website contains basic charts and stats extracted from this data.

#### Data Pipeline

- Built with [Prefect](https://www.prefect.io/) - a modern workflow orchestration tool
- Every 30 minutes it fetches data from the API in JSON format and populates the database
- JSON data is also stored on disk in compressed format (archive)
- Includes additional flows to recover data from the archive if something goes wrong, or to extract additional data (currently, only downloads and versions are tracked, but it's possible to extract all available data from the archive - this is a point for future improvement)

#### Website

- `/` - Main page with simple search by addon name, addon ID, or author name
- `/author/<author_name>` - Page for a particular author
- `/addon/<addon_id>` - Page for a particular addon
    - Additionally includes information about addon versions and a 'downloads per hour' chart