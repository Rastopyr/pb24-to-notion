# pb24-to-notion

Simple python script for export `Privat24` spending operations to `Notion` collection.

## Getting started

These instructions will get you prepare envinronment and setup script configuration.

### Prerequisites

This script require created `merchant` in `Privat24` and database block in `Notion`.

* [Notion database types](https://www.notion.so/Writing-editing-basics-68c7c67047494fdb87d50185429df93e#bff749e098814c7483ce57f0dd6ab09b)
* [How to create merchant  in Privat24](https://api.privatbank.ua/#p24/registration)

`Notion` database block should contain next fields:

* `op_id` - id of operation
* `description` - description of operation
* `terminal` - terminal description. could help identify source of operation
* `amount` - amount in UAH currency

Database block could contain any other fields. Adding of new rows will not affect them.

### Installing

For correct script working need install few dependencies:

```bash
pip install notion xmltodict requests
```

### Configuration

Repository contain configuraion file. This configuration file contain two configuration sections: `pb24` and `notion`.

**pb24**
* `merchantID` - ID of merchant. This option you will get after setup merchant in `Privat24`
* `merchantPassword` - password of merchant. This option you will get after setup merchant in `Privat24`
* `card` - card number of attached merchant.

**notion**
* `token` - `token_v2` cookie value. This value should be taken from valid session of Notion in browser
* `collectionURL` - url of database block

```json
{
    "pb24": {
        "merchantID": "",
        "card": "",
        "merchantPassword": ""
    },
    "notion": {
        "token": "",
        "collectionURL": ""
    }
}
```

### Running

For run export process just run next command

```bash
python pb24-to-notion.py
```

### Amount normalization

If bank operation was in non-UAH currency, this script use currency `Privat24` currency archive.

Amount of this operation will convert to UAH used currency exchange rate of date of this operation.
