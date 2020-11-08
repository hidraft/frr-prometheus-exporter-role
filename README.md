Role Name
=========

Prometheus exporter for FRRouting

Requirements
------------

- FRRouting

Example Playbook
----------------

- hosts: servers
  become: true
  roles:
    - frr-prometheus-exporter-role

License
-------

BSD

