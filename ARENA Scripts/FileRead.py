# Import
import json
import os
import glob
from arena import *
import scapy.all as scapy

# Global vars
scene = Scene(host="arenaxr.org", scene="demo7")
path = "/Users/Anant/UIUC Research/ArenaXR/PacketCapture.pcap"
index = 0
relations = {}
nodes = {}



#Device Representation
class Point:
    def __init__(self, sphere_position, sphere_color, mac_address):
        self.mac_address = mac_address

        self.sphere = Sphere(
            scale=Scale(0.1, 0.1, 0.1), position=sphere_position, color=sphere_color, clickable=True, persist=True,
            textinput=TextInput(
                on="mousedown",
                title="What is the mac address of this node?",
                label="Please enter below:",
                placeholder="00:11:22:33:44:55"),
            evt_handler=self.rename
        )

        self.text = Text(text=mac_address, scale=Scale(0.5, 0.5, 0.5), position=(sphere_position.x,
                        sphere_position.y+0.4, sphere_position.z))

        scene.add_object(self.sphere)
        #scene.add_object(self.text)

    def rename(self, scene, evt, msg):
        if evt.type == "textinput":
            if evt.data.text == "delete":
                if self.mac_address != "No MAC address provided":
                    nodes[self.mac_address] = None
                scene.delete_object(self.text)
                scene.delete_object(self.sphere)
            else:
                if self.text != "No MAC address provided":
                    nodes[self.text] = None
                self.mac_address = evt.data.text
                nodes[self.mac_address] = self
                self.text.update_attributes(text=self.mac_address)
                #scene.update_object(self.text)
                print(nodes.get("hi"))

#Create AR access point node
def ap_create(scene, evt, msg):
    if evt.type == "mousedown":
        Point(sphere_position=Position(evt.data.position.x-0.5, evt.data.position.y-0.05, evt.data.position.z), sphere_color=Color(
            200, 50, 50), mac_address="No MAC address provided")

#Create AR client node
def cli_create(scene, evt, msg):
    if evt.type == "mousedown":
        Point(sphere_position=Position(evt.data.position.x-0.5, evt.data.position.y+0.05, evt.data.position.z), sphere_color=Color(
            50, 50, 200), mac_address="No MAC address provided")

#VR GUI
def user_join_callback(scene, cam, msg):
    if "camera" in cam.object_id:
        ap_button = Circle(
            parent=cam.object_id,
            position=(0.25, 0.05, -.5),
            scale=(0.02, 0.02, 0.02),
            color=(100, 0, 0),
            clickable=True,
            evt_handler=ap_create
        )
        ap_text = Text(
            text="Click to place \n access point",
            parent=cam.object_id,
            position=(0.25, 0.02, -.5),
            scale=(0.05, 0.05, 0.05),
            color=(200, 100, 100)
        )
        cli_button = Circle(
            parent=cam.object_id,
            position=(0.25, -0.05, -.5),
            scale=(0.02, 0.02, 0.02),
            color=(0, 0, 100),
            clickable=True,
            evt_handler=cli_create
        )
        cli_text = Text(
            text="Click to place \n client device",
            parent=cam.object_id,
            position=(0.25, -0.08, -.5),
            scale=(0.05, 0.05, 0.05),
            color=(100, 100, 200)
        )
        scene.add_object(ap_button)
        scene.add_object(ap_text)
        scene.add_object(cli_button)
        scene.add_object(cli_text)

scene.user_join_callback = user_join_callback

#Wireshark used for packet monitoring for compatiability
#If compatible with development device, PCAP file read can be replaced with scapy.sniff(monitor = True) with the appropriate packet handler
@scene.run_forever(interval_ms=1000)
def Visualize():
    global index
    global relations
    global nodes
    packets = scapy.rdpcap(path)
    size = len(packets)
    packets = packets[index:]
    index = size
    if len(packets) == 0:
        print("No packets found")
        return 
    packet_count = {}

    for packet in packets:
        if packet.haslayer('Ether'):
            source_mac = packet['Ether'].src
            destination_mac = packet['Ether'].dst
            packet_key = (source_mac, destination_mac)
            if packet_key not in packet_count:
                    packet_count[packet_key] = 1
            packet_count[packet_key] += 1
        elif packet.haslayer('RadioTap') and packet.haslayer('Dot11'):
            source_mac = packet['Dot11'].addr2
            destination_mac = packet['Dot11'].addr1
            packet_key = (source_mac, destination_mac)
            if packet_key not in packet_count:
                packet_count[packet_key] = 1
            packet_count[packet_key] += 1
    result_data = [(source, dest, count) for (source, dest), count in packet_count.items()]
    print("result data:")
    print(result_data)

    for sorted_packets in result_data:
        source_pos = nodes.get(sorted_packets[0])
        dest_pos = nodes.get(sorted_packets[1])
        if source_pos != None and dest_pos != None:
            writing = str(sorted_packets[2]) + " packets"
            if relations.get((sorted_packets[0], sorted_packets[1])) == None:
                relations[(sorted_packets[0], sorted_packets[1])] = ThickLine(path=[source_pos.sphere.data.position, dest_pos.sphere.data.position], lineWidth=5, color=(200, 50, 200), persist=True)
                scene.add_object(
                    relations[(sorted_packets[0], sorted_packets[1])])
            pkt = Sphere(color=Color(0, 100, 0), position=source_pos.sphere.data.position, persist=True, ttl=1, scale=Scale(0.1, 0.1, 0.1), animation=Animation(
                property="position", start=source_pos.sphere.data.position, end=dest_pos.sphere.data.position, easing="linear", dur=1000))
            txt = Text(text=writing, position=source_pos.text.data.position, persist=True, ttl=1, scale=Scale(1, 1, 1), animation=Animation(
                property="position", start=source_pos.text.data.position, end=dest_pos.text.data.position, easing="linear", dur=1000))
            scene.add_object(pkt)
            scene.add_object(txt)


scene.run_tasks()
