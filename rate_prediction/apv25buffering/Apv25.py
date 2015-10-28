import config
from Buffer import Buffer

class Apv25:
    description = "Model for APV25 readout"
    buffers = []
    def __init__(self,roTime,buffer_depth):
        self.roTime = roTime
        self.depth = buffer_depth
    
    def buffer_is_full(self):
        if len(self.buffers)==self.depth:
            return True
        else:
            return False
    
    def get_dead_time(self):
        #find the time until a new trigger can be accepted
        #Assuming all have the same roTime
        #Find the earliest and latest start time
        if not self.buffer_is_full(): return 0
        t_earliest = 99999.
        t_latest = -99999.
        for buf in self.buffers:
            if buf.start_time<t_earliest: t_earliest=buf.start_time
            if buf.start_time>t_latest: t_latest=buf.start_time
        dead_time = self.roTime-(t_latest-t_earliest)
        return dead_time
    
    def update_buffers(self,time):
        # Remove buffers that are readout at this time
        if config.debug:
            print 'Updating %d buffers' % len(self.buffers)
            self.print_buffer_status()
        if len(self.buffers)==0:
            if config.debug:
                print 'No buffers to update'
            return 0
        newbuffer = []
        nRO = 0
        for buf in self.buffers:
            if time>=self.get_stop_time(buf): nRO=nRO+1
            else: newbuffer.append(buf)
        self.buffers = newbuffer
        #self.buffers = [ buf for buf in self.buffers if time<self.get_stop_time(buf)]        
        if config.debug:
            print 'Removed %d buffers ' % nRO
            self.print_buffer_status()
        return nRO
    
                
    def trigger(self,time):
        #add trigger to buffer if valid
        if config.debug:
            print 'trigger the apv25 at time %f' % (time)
        #self.update_buffers(time)
        n_buffers = len(self.buffers)
        accept = False
        if self.buffer_is_full():
        #if n_buffers>=self.depth:
            if config.debug:
                print 'buffer is full-> skip trigger!'
            accept = False
        else:
            if config.debug:
                print 'buffer is ok-> add trigger to buffer!'
            accept = True
            buf = Buffer(time)
            self.buffers.append(buf)
        return accept
    
    def get_stop_time(self,buf):
        return buf.start_time + self.roTime
    
    def print_buffer_status(self):
        if(len(self.buffers)==0):
            print 'Buffer status: empty'
        else:
            print 'Buffer status (nr=%d)' % len(self.buffers)
            for ibuf in range(len(self.buffers)):
                print '%d [%f,%f]' % (ibuf,self.buffers[ibuf].start_time,self.get_stop_time(self.buffers[ibuf]))
    
    def rollaround(self,buf):
        # readjust the time to apply to the new period
        buf.start_time = buf.start_time-self.roTime

    def rollaroundbuffers(self,time):
        # readjust the time to apply to the new period
        if config.debug:
            print 'roll around %d buffers' % len(self.buffers)
        #self.update_buffers(time)
        for buf in self.buffers:
            buf.start_time = 0 - (time-buf.start_time)
            if buf.start_time>0:
                print 'Error: the new start time is positive %f ' % (buf.start_time)
                exit(1)
        if config.debug:
            self.print_buffer_status()
    def clear_buffers(self):
        self.buffers = []
