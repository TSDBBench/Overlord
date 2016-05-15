#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <getopt.h>

int open_or_die(char *path) {
	int file, flags = O_CREAT | O_WRONLY | O_APPEND;
	if ((NULL == path) || (-1 == (file = open (path, flags, 0666)))) {
        	(void) fprintf (stderr, "Failed to open file \"%s\": %s\n", path,
                                    strerror(errno));
	       exit (EXIT_FAILURE);
	}
	return file;
}

int main (int argc, char *argv[]) {	
	// Check for some args.
	if (8 > argc) {
		(void) puts(
			"Usage: daemonize options path [args]\n"
			"\t-e <filename>  Redirect stderr to file <filename>\n"
			"\t-o <filename>  Redirect stdout to file <filename>\n"
			"\t-p <filename>  Write pid to <filename>\n");
		exit (EXIT_FAILURE);
	}
	
	// Parse args.
	int option;
	char **command = NULL, *pid_filename, *stdout_filename,
               *stderr_filename = NULL;
	while (-1 != (option = getopt (argc, argv, "+e:o:p:"))) {
		switch (option) {
 			case 'e': stderr_filename = optarg; break;
			case 'o': stdout_filename = optarg; break;
			case 'p': pid_filename = optarg; break;
			default: (void) fprintf (stderr, "Unknown option: -%c\n",
                                                        optopt);
		}
	}
       // Assume the command to daemonize is the rest of the arguments
	command = &argv[optind]; 	

	// Make a token attempt to see if we'll be able to exec the command.
	if (-1 == access (command[0], F_OK)) {
		(void) fprintf (stderr, "Can't access %s, exiting.", command[0]);
		exit (EXIT_FAILURE);
	}

	// Try to open some files for pid, stdin, stdout, stderr.
	FILE *pid_file = fopen (pid_filename, "w+");
	int stdin_file = open_or_die("/dev/null");
	int stderr_file = open_or_die(stderr_filename);
	int stdout_file = open_or_die(stdout_filename);
	
	// Nuke stdin and redirect stderr, stdout.
	close (STDIN_FILENO);
	dup2 (stdin_file, STDIN_FILENO);
	close (STDOUT_FILENO);
	dup2 (stdout_file, STDOUT_FILENO);
	close (STDERR_FILENO);
 	dup2 (stderr_file, STDERR_FILENO);

   	// Now daemonize..
	if (0 != daemon (0, 1))  {
		(void) fprintf (stderr, "Can't daemonize: %s\nExiting.",
                                   strerror(errno));
		exit (EXIT_FAILURE);
	}
	
	// Write the pid
	fprintf (pid_file, "%d\n", getpid ());
	fclose (pid_file);

	// And away we go..
	execvp (command[0], command);
}
