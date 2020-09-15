extern crate midir;

use std::error::Error;
use std::process;

use midir::{MidiOutput};

fn main() {
    match run() {
        Ok(_) => (),
        Err(err) => {
            println!("Error: {}", err);
            process::exit(1);
        }
    }
}

fn run() -> Result<(), Box<dyn Error>> {
    let midi_out = MidiOutput::new("midir test output")?;

    println!("\n{} available output ports", midi_out.ports().len());
    for (i, p) in midi_out.ports().iter().enumerate() {
        println!("    {}: {}", i, midi_out.port_name(p)?);
    }

    Ok(())
}
